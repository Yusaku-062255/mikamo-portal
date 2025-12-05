"""
AI利用状況API

管理者向けのAI利用統計情報を提供する。
テナント単位・ティア単位の利用状況を集計し、コスト可視化に活用。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.core.database import get_session
from app.models.ai_usage_log import AiUsageLog
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


# ============================================================
# レスポンスモデル
# ============================================================

class TierUsageSummary(BaseModel):
    """ティア別利用サマリー"""
    tier: str
    call_count: int
    tokens_input_total: int
    tokens_output_total: int


class DailyUsageSummary(BaseModel):
    """日別利用サマリー"""
    date: str
    tier: str
    call_count: int
    tokens_input_total: int
    tokens_output_total: int


class AiUsageSummaryResponse(BaseModel):
    """AI利用状況サマリーレスポンス"""
    period_start: str
    period_end: str
    total_calls: int
    total_tokens_input: int
    total_tokens_output: int
    by_tier: List[TierUsageSummary]
    by_day: List[DailyUsageSummary]


class PurposeUsageSummary(BaseModel):
    """用途別利用サマリー"""
    purpose: str
    call_count: int
    tokens_input_total: int
    tokens_output_total: int


class AiUsageDetailResponse(BaseModel):
    """AI利用状況詳細レスポンス"""
    period_start: str
    period_end: str
    by_purpose: List[PurposeUsageSummary]
    error_count: int
    success_rate: float


# ============================================================
# エンドポイント
# ============================================================

@router.get("/summary", response_model=AiUsageSummaryResponse)
async def get_ai_usage_summary(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    AI利用状況サマリーを取得（管理者・本部向け）

    Args:
        days: 集計期間（デフォルト7日間）

    Returns:
        テナント全体のAI利用統計
    """
    # 管理者または本部ロールのみアクセス可
    if current_user.role not in ["admin", "head"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者または本部ロールが必要です"
        )

    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="テナントが設定されていません"
        )

    # 集計期間
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 合計値を取得
    total_query = select(
        func.count(AiUsageLog.id).label("call_count"),
        func.coalesce(func.sum(AiUsageLog.tokens_input), 0).label("tokens_input"),
        func.coalesce(func.sum(AiUsageLog.tokens_output), 0).label("tokens_output")
    ).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date
    )
    total_result = session.exec(total_query).first()

    # ティア別集計
    tier_query = select(
        AiUsageLog.tier,
        func.count(AiUsageLog.id).label("call_count"),
        func.coalesce(func.sum(AiUsageLog.tokens_input), 0).label("tokens_input"),
        func.coalesce(func.sum(AiUsageLog.tokens_output), 0).label("tokens_output")
    ).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date
    ).group_by(AiUsageLog.tier)
    tier_results = session.exec(tier_query).all()

    by_tier = [
        TierUsageSummary(
            tier=row[0] or "unknown",
            call_count=row[1],
            tokens_input_total=row[2],
            tokens_output_total=row[3]
        )
        for row in tier_results
    ]

    # 日別・ティア別集計
    daily_query = select(
        func.date(AiUsageLog.created_at).label("date"),
        AiUsageLog.tier,
        func.count(AiUsageLog.id).label("call_count"),
        func.coalesce(func.sum(AiUsageLog.tokens_input), 0).label("tokens_input"),
        func.coalesce(func.sum(AiUsageLog.tokens_output), 0).label("tokens_output")
    ).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date
    ).group_by(
        func.date(AiUsageLog.created_at),
        AiUsageLog.tier
    ).order_by(func.date(AiUsageLog.created_at).desc())
    daily_results = session.exec(daily_query).all()

    by_day = [
        DailyUsageSummary(
            date=str(row[0]) if row[0] else "",
            tier=row[1] or "unknown",
            call_count=row[2],
            tokens_input_total=row[3],
            tokens_output_total=row[4]
        )
        for row in daily_results
    ]

    return AiUsageSummaryResponse(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        total_calls=total_result[0] if total_result else 0,
        total_tokens_input=total_result[1] if total_result else 0,
        total_tokens_output=total_result[2] if total_result else 0,
        by_tier=by_tier,
        by_day=by_day
    )


@router.get("/detail", response_model=AiUsageDetailResponse)
async def get_ai_usage_detail(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    AI利用状況詳細を取得（管理者向け）

    Args:
        days: 集計期間（デフォルト7日間）

    Returns:
        用途別の利用統計とエラー率
    """
    # 管理者ロールのみアクセス可
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者ロールが必要です"
        )

    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="テナントが設定されていません"
        )

    # 集計期間
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 用途別集計
    purpose_query = select(
        AiUsageLog.purpose,
        func.count(AiUsageLog.id).label("call_count"),
        func.coalesce(func.sum(AiUsageLog.tokens_input), 0).label("tokens_input"),
        func.coalesce(func.sum(AiUsageLog.tokens_output), 0).label("tokens_output")
    ).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date
    ).group_by(AiUsageLog.purpose)
    purpose_results = session.exec(purpose_query).all()

    by_purpose = [
        PurposeUsageSummary(
            purpose=row[0] or "unknown",
            call_count=row[1],
            tokens_input_total=row[2],
            tokens_output_total=row[3]
        )
        for row in purpose_results
    ]

    # エラー数を取得
    error_query = select(func.count(AiUsageLog.id)).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date,
        AiUsageLog.error != None
    )
    error_count = session.exec(error_query).first() or 0

    # 総呼び出し数
    total_query = select(func.count(AiUsageLog.id)).where(
        AiUsageLog.tenant_id == tenant_id,
        AiUsageLog.created_at >= start_date,
        AiUsageLog.created_at <= end_date
    )
    total_count = session.exec(total_query).first() or 0

    # 成功率を計算
    success_rate = ((total_count - error_count) / total_count * 100) if total_count > 0 else 100.0

    return AiUsageDetailResponse(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        by_purpose=by_purpose,
        error_count=error_count,
        success_rate=round(success_rate, 2)
    )

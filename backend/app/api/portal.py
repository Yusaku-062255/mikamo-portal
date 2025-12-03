"""
ポータル画面用API

各事業部門（BusinessUnit）ごとのダッシュボードデータを提供
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.models.business_unit import BusinessUnit, BusinessUnitType
from app.models.user import User
from app.models.daily_log import DailyLog
from app.api.deps import get_current_user, require_role
from datetime import date, timedelta

router = APIRouter()


class BusinessUnitResponse(BaseModel):
    """事業部門レスポンス"""
    id: int
    name: str
    type: str
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PortalSummaryResponse(BaseModel):
    """ポータルサマリーレスポンス"""
    business_unit_id: int
    business_unit_name: str
    business_unit_code: str
    total_sales: float
    total_customers: int
    total_transactions: int
    log_count: int
    period_start: str
    period_end: str

    class Config:
        from_attributes = True


@router.get("/business-units", response_model=List[BusinessUnitResponse])
async def list_business_units(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    事業部門一覧を取得
    
    権限:
    - staff/manager: 自分の事業部門のみ
    - head/admin: 全部門を閲覧可能
    """
    statement = select(BusinessUnit)
    
    # テナントで絞り込み
    if current_user.tenant_id:
        statement = statement.where(BusinessUnit.tenant_id == current_user.tenant_id)
    
    # ロールに応じた権限チェック
    if current_user.role in ["staff", "manager"]:
        # 自分の事業部門のみ
        if current_user.business_unit_id:
            statement = statement.where(BusinessUnit.id == current_user.business_unit_id)
        else:
            # business_unit_idが未設定の場合は空リストを返す
            return []
    
    business_units = session.exec(statement).all()
    return business_units


@router.get("/business-units/{business_unit_id}", response_model=BusinessUnitResponse)
async def get_business_unit(
    business_unit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    事業部門情報を取得
    
    権限:
    - staff/manager: 自分の事業部門のみ閲覧可能
    - head/admin: 全部門を閲覧可能
    """
    business_unit = session.get(BusinessUnit, business_unit_id)
    if not business_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事業部門が見つかりません"
        )
    
    # テナントチェック
    if current_user.tenant_id and business_unit.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事業部門が見つかりません"
        )
    
    # 権限チェック
    if current_user.role in ["staff", "manager"]:
        if current_user.business_unit_id != business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この事業部門を閲覧する権限がありません"
            )
    
    return business_unit


@router.get("/business-units/{business_unit_id}/summary", response_model=PortalSummaryResponse)
async def get_business_unit_summary(
    business_unit_id: int,
    days: int = Query(14, description="集計期間（日数）"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    事業部門のサマリーデータを取得
    
    権限:
    - staff/manager: 自分の事業部門のみ閲覧可能
    - head/admin: 全部門を閲覧可能
    """
    business_unit = session.get(BusinessUnit, business_unit_id)
    if not business_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事業部門が見つかりません"
        )
    
    # テナントチェック
    if current_user.tenant_id and business_unit.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事業部門が見つかりません"
        )
    
    # 権限チェック
    if current_user.role in ["staff", "manager"]:
        if current_user.business_unit_id != business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この事業部門を閲覧する権限がありません"
            )
    
    # 期間を計算
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    # 日報データを集計（BusinessUnit経由で取得）
    # 後方互換性のため、Departmentのcodeからも検索可能にする
    from app.models.user import Department
    statement = select(Department).where(Department.code == business_unit.code)
    department = session.exec(statement).first()
    
    if not department:
        # Departmentが見つからない場合は空のサマリーを返す
        return PortalSummaryResponse(
            business_unit_id=business_unit.id,
            business_unit_name=business_unit.name,
            business_unit_code=business_unit.code,
            total_sales=0.0,
            total_customers=0,
            total_transactions=0,
            log_count=0,
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat()
        )
    
    # 日報データを集計
    statement = select(DailyLog).where(
        DailyLog.department_id == department.id,
        DailyLog.log_date >= start_date,
        DailyLog.log_date <= end_date
    )
    logs = session.exec(statement).all()
    
    total_sales = sum(log.sales_amount for log in logs)
    total_customers = sum(log.customers_count for log in logs)
    total_transactions = sum(log.transaction_count for log in logs)
    log_count = len(logs)
    
    return PortalSummaryResponse(
        business_unit_id=business_unit.id,
        business_unit_name=business_unit.name,
        business_unit_code=business_unit.code,
        total_sales=total_sales,
        total_customers=total_customers,
        total_transactions=total_transactions,
        log_count=log_count,
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat()
    )


@router.get("/hq/summary", response_model=List[PortalSummaryResponse])
async def get_hq_summary(
    days: int = Query(14, description="集計期間（日数）"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    本部ビュー: 全部門のサマリーデータを取得

    権限: head/admin のみ
    """
    # テナントの全事業部門を取得
    statement = select(BusinessUnit)
    if current_user.tenant_id:
        statement = statement.where(BusinessUnit.tenant_id == current_user.tenant_id)
    
    business_units = session.exec(statement).all()
    
    # 各事業部門のサマリーを取得
    summaries = []
    for bu in business_units:
        summary = await get_business_unit_summary(
            bu.id, days, current_user, session
        )
        summaries.append(summary)
    
    return summaries


class BusinessUnitHealthResponse(BaseModel):
    """BusinessUnitHealthレスポンス"""
    business_unit_id: int
    business_unit_name: str
    risk_score: int
    opportunity_score: int
    last_updated_at: str

    class Config:
        from_attributes = True


@router.get("/hq/health", response_model=List[BusinessUnitHealthResponse])
async def get_hq_health(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    本部ビュー: 全部門の健康度スコアを取得

    権限: head/admin のみ
    """
    from app.models.business_unit_health import BusinessUnitHealth
    from app.services.business_unit_health_service import update_business_unit_health
    
    # テナントの全事業部門を取得
    statement = select(BusinessUnit)
    if current_user.tenant_id:
        statement = statement.where(BusinessUnit.tenant_id == current_user.tenant_id)
    
    business_units = session.exec(statement).all()
    
    # 各事業部門の健康度スコアを取得または更新
    health_list = []
    for bu in business_units:
        # スコアを更新
        health = update_business_unit_health(session, bu.id)
        
        health_list.append(BusinessUnitHealthResponse(
            business_unit_id=bu.id,
            business_unit_name=bu.name,
            risk_score=health.risk_score,
            opportunity_score=health.opportunity_score,
            last_updated_at=health.last_updated_at.isoformat() if health.last_updated_at else ""
        ))
    
    return health_list


from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core.database import get_session
from app.models.daily_log import DailyLog, WeatherType
from app.models.user import User
from app.api.deps import get_current_user
from app.repositories.daily_log_repository import (
    get_department_daily_logs_for_chart,
    get_all_departments_today_summary
)
from pydantic import BaseModel, Field

router = APIRouter()


class DailyLogCreate(BaseModel):
    date: date
    weather: Optional[WeatherType] = None
    sales_amount: int = 0
    customers_count: int = 0
    transaction_count: int = 0
    highlight: Optional[str] = None
    problem: Optional[str] = None
    memo: Optional[str] = None


class DailyLogUpdate(BaseModel):
    weather: Optional[WeatherType] = None
    sales_amount: Optional[int] = None
    customers_count: Optional[int] = None
    transaction_count: Optional[int] = None
    highlight: Optional[str] = None
    problem: Optional[str] = None
    memo: Optional[str] = None
    manager_comment: Optional[str] = None


class DailyLogResponse(BaseModel):
    id: int
    date: date
    department_id: int
    user_id: int
    weather: Optional[WeatherType] = None
    sales_amount: int
    customers_count: int
    transaction_count: int
    highlight: Optional[str] = None
    problem: Optional[str] = None
    memo: Optional[str] = None
    manager_comment: Optional[str] = None
    reaction_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    total_sales: int
    total_customers: int
    total_transactions: int
    log_count: int
    week_start: date
    week_end: date


class ManagerCommentRequest(BaseModel):
    comment: str = Field(..., max_length=1000, description="承認＋次の一歩のヒントを書いてください")


@router.post("", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
async def create_daily_log(
    log_data: DailyLogCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """日次ログを作成"""
    # 同じ日付のログが既に存在するかチェック
    statement = select(DailyLog).where(
        DailyLog.log_date == log_data.date,
        DailyLog.user_id == current_user.id
    )
    existing_log = session.exec(statement).first()
    if existing_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="この日付のログは既に存在します"
        )
    
    daily_log = DailyLog(
        log_date=log_data.date,
        department_id=current_user.department_id,
        user_id=current_user.id,
        weather=log_data.weather,
        sales_amount=log_data.sales_amount,
        customers_count=log_data.customers_count,
        transaction_count=log_data.transaction_count,
        highlight=log_data.highlight,
        problem=log_data.problem,
        memo=log_data.memo
    )
    session.add(daily_log)
    session.commit()
    session.refresh(daily_log)
    return daily_log


@router.get("", response_model=List[DailyLogResponse])
async def get_daily_logs(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """日次ログ一覧を取得"""
    statement = select(DailyLog).where(DailyLog.user_id == current_user.id)
    
    if start_date:
        statement = statement.where(DailyLog.log_date >= start_date)
    if end_date:
        statement = statement.where(DailyLog.log_date <= end_date)
    
    statement = statement.order_by(DailyLog.log_date.desc()).offset(skip).limit(limit)
    logs = session.exec(statement).all()
    return logs


@router.get("/{log_id}", response_model=DailyLogResponse)
async def get_daily_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """日次ログを取得"""
    statement = select(DailyLog).where(
        DailyLog.id == log_id,
        DailyLog.user_id == current_user.id
    )
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    return log


@router.patch("/{log_id}", response_model=DailyLogResponse)
async def update_daily_log(
    log_id: int,
    log_data: DailyLogUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """日次ログを更新"""
    statement = select(DailyLog).where(
        DailyLog.id == log_id,
        DailyLog.user_id == current_user.id
    )
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    
    update_data = log_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)
    
    log.updated_at = datetime.utcnow()
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """日次ログを削除"""
    statement = select(DailyLog).where(
        DailyLog.id == log_id,
        DailyLog.user_id == current_user.id
    )
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    session.delete(log)
    session.commit()
    return None


@router.get("/summary/week", response_model=SummaryResponse)
async def get_weekly_summary(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """過去1週間のサマリーを取得（今週の頑張り）"""
    today = date.today()
    week_start = today - timedelta(days=6)  # 今日を含めて7日間
    
    statement = select(
        func.sum(DailyLog.sales_amount).label("total_sales"),
        func.sum(DailyLog.customers_count).label("total_customers"),
        func.sum(DailyLog.transaction_count).label("total_transactions"),
        func.count(DailyLog.id).label("log_count")
    ).where(
        DailyLog.user_id == current_user.id,
        DailyLog.log_date >= week_start,
        DailyLog.log_date <= today
    )
    
    result = session.exec(statement).first()
    
    # 結果がNoneの場合（データがない場合）の処理
    if result is None:
        return SummaryResponse(
            total_sales=0,
            total_customers=0,
            total_transactions=0,
            log_count=0,
            week_start=week_start,
            week_end=today
        )
    
    return SummaryResponse(
        total_sales=result.total_sales or 0,
        total_customers=result.total_customers or 0,
        total_transactions=result.total_transactions or 0,
        log_count=result.log_count or 0,
        week_start=week_start,
        week_end=today
    )


@router.post("/{log_id}/react", response_model=DailyLogResponse)
async def react_to_daily_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    日次ログに「いいね」をつける（エンゲージメント機能）
    v0.2では単純にreaction_countを+1する実装
    """
    statement = select(DailyLog).where(DailyLog.id == log_id)
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    
    # いいねを追加
    log.reaction_count += 1
    log.updated_at = datetime.utcnow()
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.put("/{log_id}/manager-comment", response_model=DailyLogResponse)
async def update_manager_comment(
    log_id: int,
    comment_data: ManagerCommentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    マネージャーコメントを更新（承認＋次の一歩のヒント）
    マネージャー以上（manager, admin, head, accounting）のみアクセス可能
    """
    # 権限チェック
    allowed_roles = ["manager", "admin", "head", "accounting"]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作にはマネージャー以上の権限が必要です"
        )
    
    statement = select(DailyLog).where(DailyLog.id == log_id)
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    
    # コメントを更新（承認＋次の一歩のヒントを重視）
    log.manager_comment = comment_data.comment
    log.updated_at = datetime.utcnow()
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("/chart/trend", response_model=List[dict])
async def get_trend_chart_data(
    department_id: Optional[int] = None,
    days: int = 14,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    トレンドグラフ用データを取得（14日間）
    head/managerのみ、他部署のデータも閲覧可能
    """
    # 部署IDの決定
    target_department_id = department_id
    if target_department_id is None:
        target_department_id = current_user.department_id
    else:
        # 他部署のデータを閲覧する場合、権限チェック
        if current_user.role not in ["manager", "admin", "head"]:
            if target_department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="他部署のデータを閲覧する権限がありません"
                )
    
    return get_department_daily_logs_for_chart(session, target_department_id, days)


@router.get("/chart/departments-comparison", response_model=List[dict])
async def get_departments_comparison_data(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    部署間比較グラフ用データを取得（今日の状況）
    head/managerのみアクセス可能
    """
    if current_user.role not in ["manager", "admin", "head"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作にはマネージャー以上の権限が必要です"
        )
    
    return get_all_departments_today_summary(session)

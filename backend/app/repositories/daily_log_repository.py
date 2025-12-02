"""
DailyLog リポジトリ層
AIサービスやダッシュボードで使用するデータ取得ロジック
"""
from sqlmodel import Session, select, func, and_
from typing import List, Optional
from datetime import date, timedelta
from app.models.daily_log import DailyLog
from app.models.user import Department


def get_recent_daily_logs_by_department(
    session: Session,
    department_id: int,
    days: int = 14
) -> List[DailyLog]:
    """
    指定部署の直近N日間のDailyLogを取得
    
    Args:
        session: データベースセッション
        department_id: 部署ID
        days: 取得する日数（デフォルト14日）
    
    Returns:
        DailyLogのリスト（日付降順）
    """
    cutoff_date = date.today() - timedelta(days=days)
    statement = select(DailyLog).where(
        and_(
            DailyLog.department_id == department_id,
            DailyLog.log_date >= cutoff_date
        )
    ).order_by(DailyLog.log_date.desc())
    return list(session.exec(statement).all())


def get_daily_logs_summary_by_department(
    session: Session,
    department_id: int,
    days: int = 14
) -> dict:
    """
    指定部署の直近N日間のサマリーを取得（AIコンテキスト用）
    
    Args:
        session: データベースセッション
        department_id: 部署ID
        days: 集計する日数（デフォルト14日）
    
    Returns:
        サマリーデータの辞書
    """
    cutoff_date = date.today() - timedelta(days=days)
    statement = select(
        func.sum(DailyLog.sales_amount).label("total_sales"),
        func.sum(DailyLog.customers_count).label("total_customers"),
        func.sum(DailyLog.transaction_count).label("total_transactions"),
        func.count(DailyLog.id).label("log_count"),
        func.avg(DailyLog.sales_amount).label("avg_sales"),
        func.avg(DailyLog.customers_count).label("avg_customers"),
    ).where(
        and_(
            DailyLog.department_id == department_id,
            DailyLog.log_date >= cutoff_date
        )
    )
    result = session.exec(statement).first()
    
    if result is None:
        return {
            "total_sales": 0,
            "total_customers": 0,
            "total_transactions": 0,
            "log_count": 0,
            "avg_sales": 0.0,
            "avg_customers": 0.0,
        }
    
    return {
        "total_sales": result.total_sales or 0,
        "total_customers": result.total_customers or 0,
        "total_transactions": result.total_transactions or 0,
        "log_count": result.log_count or 0,
        "avg_sales": float(result.avg_sales or 0),
        "avg_customers": float(result.avg_customers or 0),
    }


def get_today_daily_log(
    session: Session,
    user_id: int
) -> Optional[DailyLog]:
    """
    指定ユーザーの今日のDailyLogを取得
    
    Args:
        session: データベースセッション
        user_id: ユーザーID
    
    Returns:
        DailyLog（存在しない場合はNone）
    """
    today = date.today()
    statement = select(DailyLog).where(
        and_(
            DailyLog.user_id == user_id,
            DailyLog.log_date == today
        )
    )
    return session.exec(statement).first()


def get_department_daily_logs_for_chart(
    session: Session,
    department_id: int,
    days: int = 14
) -> List[dict]:
    """
    グラフ表示用のデータを取得（日付ごとの集計）
    
    Args:
        session: データベースセッション
        department_id: 部署ID
        days: 取得する日数
    
    Returns:
        日付ごとの集計データのリスト
    """
    cutoff_date = date.today() - timedelta(days=days)
    statement = select(
        DailyLog.log_date,
        func.sum(DailyLog.sales_amount).label("sales"),
        func.sum(DailyLog.customers_count).label("customers"),
        func.sum(DailyLog.transaction_count).label("transactions"),
        func.max(DailyLog.weather).label("weather"),  # その日の代表的な天気
    ).where(
        and_(
            DailyLog.department_id == department_id,
            DailyLog.log_date >= cutoff_date
        )
    ).group_by(DailyLog.log_date).order_by(DailyLog.log_date)
    
    results = session.exec(statement).all()
    return [
        {
            "date": str(r.log_date),
            "sales": r.sales or 0,
            "customers": r.customers or 0,
            "transactions": r.transactions or 0,
            "weather": r.weather,
        }
        for r in results
    ]


def get_all_departments_today_summary(session: Session) -> List[dict]:
    """
    全部署の今日のサマリーを取得（部署間比較用）
    
    Args:
        session: データベースセッション
    
    Returns:
        部署ごとのサマリーデータのリスト
    """
    today = date.today()
    statement = select(
        Department.id,
        Department.name,
        Department.code,
        func.sum(DailyLog.sales_amount).label("sales"),
        func.sum(DailyLog.customers_count).label("customers"),
        func.sum(DailyLog.transaction_count).label("transactions"),
        func.count(DailyLog.id).label("log_count"),
    ).join(
        DailyLog, DailyLog.department_id == Department.id
    ).where(
        DailyLog.log_date == today
    ).group_by(Department.id, Department.name, Department.code)
    
    results = session.exec(statement).all()
    return [
        {
            "department_id": r.id,
            "department_name": r.name,
            "department_code": r.code,
            "sales": r.sales or 0,
            "customers": r.customers or 0,
            "transactions": r.transactions or 0,
            "log_count": r.log_count or 0,
        }
        for r in results
    ]


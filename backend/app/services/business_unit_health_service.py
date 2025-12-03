"""
BusinessUnitHealth計算サービス

各事業部門のリスクスコア・機会スコアを計算
"""
from sqlmodel import Session, select, func
from typing import Dict
from app.models.business_unit_health import BusinessUnitHealth
from app.models.issue import Issue, IssueTopic, IssueStatus
from app.models.insight import Insight, InsightType
from app.models.daily_log import DailyLog
from app.models.business_unit import BusinessUnit
import structlog

logger = structlog.get_logger()


def calculate_business_unit_health(
    session: Session,
    business_unit_id: int
) -> Dict[str, int]:
    """
    事業部門の健康度スコアを計算
    
    Args:
        session: データベースセッション
        business_unit_id: 事業部門ID
    
    Returns:
        {
            "risk_score": 0-100,
            "opportunity_score": 0-100
        }
    """
    risk_score = 0
    opportunity_score = 0
    
    # 1. Issueベースのスコア計算
    # 将来リスク系Issueが少ない = 危機感が薄い = リスクを上げる
    future_risk_issues = session.exec(
        select(func.count(Issue.id)).where(
            Issue.business_unit_id == business_unit_id,
            Issue.topic == IssueTopic.FUTURE_RISK,
            Issue.status != IssueStatus.RESOLVED
        )
    ).first() or 0
    
    if future_risk_issues == 0:
        # 将来リスクに関するIssueが全くない = 危機感が薄い可能性
        risk_score += 20
    
    # クレーム系Issueが多い = リスクを上げる
    complaint_issues = session.exec(
        select(func.count(Issue.id)).where(
            Issue.business_unit_id == business_unit_id,
            Issue.topic == IssueTopic.CUSTOMER_COMPLAINT,
            Issue.status != IssueStatus.RESOLVED
        )
    ).first() or 0
    
    if complaint_issues >= 3:
        risk_score += min(30, complaint_issues * 5)
    
    # 2. Insightベースのスコア計算
    # リスクタイプのInsightが多い = リスクを上げる
    risk_insights = session.exec(
        select(func.sum(Insight.score)).where(
            Insight.business_unit_id == business_unit_id,
            Insight.type == InsightType.RISK
        )
    ).first() or 0
    
    risk_score += min(30, risk_insights // 10)
    
    # 機会タイプのInsightが多い = 機会スコアを上げる
    opportunity_insights = session.exec(
        select(func.sum(Insight.score)).where(
            Insight.business_unit_id == business_unit_id,
            Insight.type == InsightType.OPPORTUNITY
        )
    ).first() or 0
    
    opportunity_score += min(40, opportunity_insights // 10)
    
    # 売上機会系Issueが多い = 機会スコアを上げる
    sales_opportunity_issues = session.exec(
        select(func.count(Issue.id)).where(
            Issue.business_unit_id == business_unit_id,
            Issue.topic == IssueTopic.SALES_OPPORTUNITY,
            Issue.status != IssueStatus.RESOLVED
        )
    ).first() or 0
    
    opportunity_score += min(30, sales_opportunity_issues * 10)
    
    # 3. 日報データベースのスコア計算（将来的に会計連携）
    # 現時点では簡易的に、日報の投稿頻度で判断
    # DailyLogはbusiness_unit_idを持たないため、Department経由で取得
    from app.models.user import Department
    business_unit = session.get(BusinessUnit, business_unit_id)
    if business_unit:
        department = session.exec(
            select(Department).where(Department.code == business_unit.code)
        ).first()
        if department:
            recent_logs_count = session.exec(
                select(func.count(DailyLog.id)).where(
                    DailyLog.department_id == department.id
                )
            ).first() or 0
        else:
            recent_logs_count = 0
    else:
        recent_logs_count = 0
    
    if recent_logs_count > 10:
        # 日報が活発 = 現場のエンゲージメントが高い = 機会スコアを上げる
        opportunity_score += min(20, recent_logs_count // 2)
    
    # スコアを0-100の範囲に正規化
    risk_score = min(100, max(0, risk_score))
    opportunity_score = min(100, max(0, opportunity_score))
    
    return {
        "risk_score": risk_score,
        "opportunity_score": opportunity_score
    }


def update_business_unit_health(
    session: Session,
    business_unit_id: int
) -> BusinessUnitHealth:
    """
    事業部門の健康度スコアを更新
    
    Args:
        session: データベースセッション
        business_unit_id: 事業部門ID
    
    Returns:
        BusinessUnitHealthオブジェクト
    """
    scores = calculate_business_unit_health(session, business_unit_id)
    
    # 既存のレコードを取得または作成
    health = session.exec(
        select(BusinessUnitHealth).where(
            BusinessUnitHealth.business_unit_id == business_unit_id
        )
    ).first()
    
    if not health:
        health = BusinessUnitHealth(
            business_unit_id=business_unit_id,
            risk_score=scores["risk_score"],
            opportunity_score=scores["opportunity_score"]
        )
        session.add(health)
    else:
        health.risk_score = scores["risk_score"]
        health.opportunity_score = scores["opportunity_score"]
        from datetime import datetime
        health.last_updated_at = datetime.utcnow()
        session.add(health)
    
    session.commit()
    session.refresh(health)
    
    logger.info(
        "BusinessUnitHealth updated",
        business_unit_id=business_unit_id,
        risk_score=scores["risk_score"],
        opportunity_score=scores["opportunity_score"]
    )
    
    return health


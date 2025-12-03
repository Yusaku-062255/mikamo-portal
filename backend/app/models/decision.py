"""
Decision（経営・マネージャー側の意思決定ログ）モデル

HQが下す意思決定を履歴として残し、Issue/Insightと紐づける
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Text
from enum import Enum


class DecisionStatus(str, Enum):
    """Decisionのステータス"""
    PLANNED = "planned"  # 計画中
    IN_PROGRESS = "in_progress"  # 進行中
    DONE = "done"  # 完了
    CANCELLED = "cancelled"  # キャンセル


class Decision(SQLModel, table=True):
    """Decisionモデル（経営・マネージャー側の意思決定ログ）"""
    __tablename__ = "decisions"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )  # nullなら全社
    title: str = Field(index=True)
    content: str = Field(sa_column=Column(Text))  # どんな判断をしたか／何をいつまでにやるか
    status: DecisionStatus = Field(default=DecisionStatus.PLANNED, index=True)
    created_by_user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship()
    business_unit: Optional["BusinessUnit"] = Relationship()
    created_by: "User" = Relationship()
    # 中間テーブル経由の関係は後で実装（一旦シンプルに）


# 中間テーブル: InsightとDecisionの多対多関係（将来的に実装）
# from sqlmodel import Table, Column as SQLColumn, Integer, ForeignKey
# 
# insight_decision_link = Table(
#     "insight_decision_link",
#     SQLModel.metadata,
#     SQLColumn("insight_id", Integer, ForeignKey("insights.id"), primary_key=True),
#     SQLColumn("decision_id", Integer, ForeignKey("decisions.id"), primary_key=True),
# )


"""
Insight（AIによる分析・提案）モデル

多数のIssueや会話ログから、AIが抽出した「こうした方がいいのでは？」を構造化して保存
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional
from datetime import datetime
from sqlalchemy import Text
from enum import Enum


class InsightType(str, Enum):
    """Insightのタイプ"""
    RISK = "risk"  # リスク
    OPPORTUNITY = "opportunity"  # 機会
    IMPROVEMENT = "improvement"  # 改善提案


class Insight(SQLModel, table=True):
    """Insightモデル（AIによる分析・提案）"""
    __tablename__ = "insights"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )  # nullなら全社
    title: str = Field(index=True)  # 提案・気付きの要約
    content: str = Field(sa_column=Column(Text))  # AIが生成した提案・分析
    type: InsightType = Field(index=True)
    score: int = Field(default=0, index=True)  # 0〜100の重要度スコア
    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id"
    )  # 基本はAIだが、人間が追記・修正できる前提
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship()
    business_unit: Optional["BusinessUnit"] = Relationship()
    creator: Optional["User"] = Relationship()
    # related_issues は中間テーブル未実装のため一旦コメントアウト
    # 将来的に多対多関係として実装予定


# 中間テーブル: IssueとInsightの多対多関係（将来的に実装）
# from sqlmodel import Table, Column as SQLColumn, Integer, ForeignKey
# 
# issue_insight_link = Table(
#     "issue_insight_link",
#     SQLModel.metadata,
#     SQLColumn("issue_id", Integer, ForeignKey("issues.id"), primary_key=True),
#     SQLColumn("insight_id", Integer, ForeignKey("insights.id"), primary_key=True),
# )


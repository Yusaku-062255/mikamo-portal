"""
Issue（現場での"困りごと"・トピック）モデル

従業員がAIに質問した内容から、AIが自動的にIssueを起票する
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Text
from enum import Enum


class IssueStatus(str, Enum):
    """Issueのステータス"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class IssueTopic(str, Enum):
    """Issueのトピック"""
    MENU = "menu"  # メニュー・レシピ
    OPERATION = "operation"  # オペレーション・手順
    CUSTOMER_COMPLAINT = "customer_complaint"  # クレーム
    FUTURE_RISK = "future_risk"  # 将来リスク
    SALES_OPPORTUNITY = "sales_opportunity"  # 売上機会
    STAFFING = "staffing"  # 人員・採用
    OTHER = "other"  # その他


class Issue(SQLModel, table=True):
    """Issueモデル（現場での"困りごと"・トピック）"""
    __tablename__ = "issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )
    title: str = Field(index=True)  # AI or ユーザーが付ける要約タイトル
    description: str = Field(sa_column=Column(Text))  # 質問内容・状況
    status: IssueStatus = Field(default=IssueStatus.OPEN, index=True)
    topic: IssueTopic = Field(default=IssueTopic.OTHER, index=True)
    created_by_user_id: int = Field(foreign_key="users.id", index=True)
    conversation_id: Optional[int] = Field(
        default=None,
        foreign_key="conversations.id",
        index=True
    )  # 関連するAIチャットがある場合
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship()
    business_unit: Optional["BusinessUnit"] = Relationship()
    created_by: "User" = Relationship()
    conversation: Optional["Conversation"] = Relationship()
    # 中間テーブル経由の関係は後で実装（一旦シンプルに）


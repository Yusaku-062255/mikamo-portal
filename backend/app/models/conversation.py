"""
会話履歴モデル

AIアシスタントとの会話を管理するためのモデル
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Text


class Conversation(SQLModel, table=True):
    """会話モデル（会話セッション）"""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )
    title: Optional[str] = None  # 会話のタイトル（最初のメッセージから自動生成）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship()
    user: "User" = Relationship()
    business_unit: Optional["BusinessUnit"] = Relationship()
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """メッセージモデル（会話内の個別メッセージ）"""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    role: str = Field(index=True)  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")


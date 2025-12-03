"""
テナントモデル（将来のマルチテナント対応）

現時点では株式会社ミカモのみを想定（tenant_id = 'mikamo'）
将来的に他社にも展開できるよう、テナント概念を導入
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Tenant(SQLModel, table=True):
    """テナントモデル（会社単位）"""
    __tablename__ = "tenants"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # "mikamo"
    display_name: str  # "株式会社ミカモ"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    business_units: List["BusinessUnit"] = Relationship(back_populates="tenant")
    users: List["User"] = Relationship(back_populates="tenant")
    knowledge_items: List["KnowledgeItem"] = Relationship(back_populates="tenant")
    conversations: List["Conversation"] = Relationship(back_populates="tenant")


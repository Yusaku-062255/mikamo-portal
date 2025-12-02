from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


class AIChatLog(SQLModel, table=True):
    """AI相談ログモデル"""
    __tablename__ = "ai_chat_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    question: str
    answer: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="ai_chat_logs")


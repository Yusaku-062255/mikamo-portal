from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Department(SQLModel, table=True):
    """部署モデル"""
    __tablename__ = "departments"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)  # "gas", "coating", "cafe", "head", "mnet"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: List["User"] = Relationship(back_populates="department")
    daily_logs: List["DailyLog"] = Relationship(back_populates="department")


class User(SQLModel, table=True):
    """ユーザーモデル"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    department_id: int = Field(foreign_key="departments.id")
    role: str = Field(default="staff")  # "staff", "manager", "admin"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    department: Department = Relationship(back_populates="users")
    daily_logs: List["DailyLog"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    ai_chat_logs: List["AIChatLog"] = Relationship(back_populates="user")


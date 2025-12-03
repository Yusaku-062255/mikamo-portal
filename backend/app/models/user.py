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
    tenant_id: Optional[int] = Field(
        default=None,
        foreign_key="tenants.id",
        index=True
    )  # 将来のマルチテナント対応（現時点では常にmikamo）
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    department_id: int = Field(foreign_key="departments.id")  # 後方互換性のため残す
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )  # 新しいBusinessUnitへの参照
    role: str = Field(default="staff")  # "staff", "manager", "head", "admin"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    department: Department = Relationship(back_populates="users")  # 後方互換性
    business_unit: Optional["BusinessUnit"] = Relationship(back_populates="users")
    daily_logs: List["DailyLog"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    ai_chat_logs: List["AIChatLog"] = Relationship(back_populates="user")
    conversations: List["Conversation"] = Relationship(back_populates="user")


"""
事業部門モデル（BusinessUnit）

既存のDepartmentモデルを拡張し、テナント対応とより明確な型定義を追加
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BusinessUnitType(str, Enum):
    """事業部門タイプ"""
    GAS_STATION = "gas_station"  # ミカモ石油（ガソリンスタンド）
    CAR_COATING = "car_coating"  # カーコーティング事業（SOUP）
    USED_CAR = "used_car"  # 中古車販売
    CAFE = "cafe"  # ミカモ喫茶（カフェ）
    HQ = "hq"  # 本部（経営・経理・全社方針）


class BusinessUnit(SQLModel, table=True):
    """事業部門モデル"""
    __tablename__ = "business_units"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    name: str = Field(index=True)  # "ミカモ石油（ガソリンスタンド）"
    type: BusinessUnitType = Field(index=True)  # BusinessUnitType enum
    code: str = Field(unique=True, index=True)  # "gas", "coating", "cafe", "head", "mnet"（後方互換性のため）
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship(back_populates="business_units")
    users: List["User"] = Relationship(back_populates="business_unit")
    knowledge_items: List["KnowledgeItem"] = Relationship(back_populates="business_unit")
    daily_logs: List["DailyLog"] = Relationship(back_populates="business_unit")
    conversations: List["Conversation"] = Relationship(back_populates="business_unit")


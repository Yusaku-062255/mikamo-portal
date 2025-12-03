"""
BusinessUnitHealth（事業部門の健康度スコア）モデル

各事業部門のリスクスコア・機会スコアを管理
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


class BusinessUnitHealth(SQLModel, table=True):
    """BusinessUnitHealthモデル（事業部門の健康度スコア）"""
    __tablename__ = "business_unit_health"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_unit_id: int = Field(
        foreign_key="business_units.id",
        unique=True,
        index=True
    )
    risk_score: int = Field(default=0)  # 0〜100のリスクスコア
    opportunity_score: int = Field(default=0)  # 0〜100の機会スコア
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    business_unit: "BusinessUnit" = Relationship()


from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date as date_type, datetime
from enum import Enum


class WeatherType(str, Enum):
    """天気タイプ"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOW = "snow"


class DailyLog(SQLModel, table=True):
    """日次ログモデル（強化版）"""
    __tablename__ = "daily_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    log_date: date_type = Field(index=True, sa_column_kwargs={"name": "date"})
    department_id: int = Field(foreign_key="departments.id")
    user_id: int = Field(foreign_key="users.id")
    
    # 環境データ
    weather: Optional[WeatherType] = None
    
    # KPIデータ
    sales_amount: int = Field(default=0)
    customers_count: int = Field(default=0)
    transaction_count: int = Field(default=0)
    
    # 定性データ
    highlight: Optional[str] = None  # Good
    problem: Optional[str] = None  # Bad/Challenge
    memo: Optional[str] = None
    
    # エンゲージメント
    manager_comment: Optional[str] = None  # マネージャーからのコメント（承認＋次の一歩のヒント）
    reaction_count: int = Field(default=0)  # 「いいね」の数
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    # Relationships
    department: "Department" = Relationship(back_populates="daily_logs")
    user: "User" = Relationship(back_populates="daily_logs")


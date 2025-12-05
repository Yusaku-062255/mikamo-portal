"""
ナレッジアイテムモデル

ミカモグループの社内情報（レシピ、オペレーションメモ、キャンペーン振り返り、マニュアル、経営方針など）
を蓄積し、AIが参照できるナレッジベース
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Text, ARRAY, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY


class KnowledgeItem(SQLModel, table=True):
    """ナレッジアイテムモデル"""
    __tablename__ = "knowledge_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    business_unit_id: Optional[int] = Field(
        default=None,
        foreign_key="business_units.id",
        index=True
    )  # どの事業部の情報か。全社共通 → None または hq
    title: str = Field(index=True)
    content: str = Field(sa_column=Column(Text))  # Markdown or プレーンテキスト
    category: Optional[str] = Field(default=None, index=True)  # カテゴリ（例：DXレポート、レシピ、マニュアル）
    source: Optional[str] = Field(default=None)  # 情報元（例：Claude調査、社内資料）
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(PG_ARRAY(String))
    )  # タグ（文字列配列）
    created_by: int = Field(foreign_key="users.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    is_active: bool = Field(default=True, index=True)  # 有効/無効フラグ（ソフトデリート用）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 将来的にベクトル検索（RAG）を行うことを想定
    # embedding_vector: Optional[List[float]] = None  # 別テーブル or 外部ベクタDB前提でも可

    # Relationships
    tenant: "Tenant" = Relationship(back_populates="knowledge_items")
    business_unit: Optional["BusinessUnit"] = Relationship(back_populates="knowledge_items")
    # SQLModelでは複数のFKを持つ場合、sa_relationship_kwargsでforeign_keysを指定
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[KnowledgeItem.created_by]"}
    )
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[KnowledgeItem.updated_by]"}
    )


"""
テナントモデル（マルチテナント対応）

SaaS型DXプラットフォームとして、複数企業（テナント）をサポート。
各テナントは独自のブランド設定、AIポリシー、事業部門構成を持つ。
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.models.business_unit import BusinessUnit
    from app.models.user import User
    from app.models.knowledge_item import KnowledgeItem
    from app.models.conversation import Conversation


class AiTierPolicy(str, Enum):
    """テナントごとのAIティア利用ポリシー"""
    ALL = "all"                    # 全ティア利用可能（BASIC/STANDARD/PREMIUM）
    STANDARD_MAX = "standard_max"  # STANDARD以下のみ（BASIC/STANDARD）
    BASIC_ONLY = "basic_only"      # BASICのみ（コスト重視プラン）


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
    settings: Optional["TenantSettings"] = Relationship(back_populates="tenant")


class TenantSettings(SQLModel, table=True):
    """
    テナント設定モデル

    テナントごとのブランド設定、AIポリシー、UI設定を管理。
    SaaS展開時に、テナントごとに異なる見た目・機能制限を実現する。
    """
    __tablename__ = "tenant_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", unique=True, index=True)

    # ========================================
    # ブランド設定
    # ========================================
    logo_url: Optional[str] = Field(default=None)  # ロゴ画像URL
    primary_color: str = Field(default="#3B82F6")  # プライマリカラー（Tailwind blue-500）
    secondary_color: str = Field(default="#1E40AF")  # セカンダリカラー（Tailwind blue-800）

    # ========================================
    # AI設定
    # ========================================
    ai_tier_policy: AiTierPolicy = Field(default=AiTierPolicy.ALL)
    # AIプロンプトに含める会社説明（システムプロンプトで使用）
    ai_company_context: str = Field(
        default="このテナントの従業員向けAIアシスタントです。"
    )
    # AI応答の最大トークン数（テナント別に制限可能）
    ai_max_tokens_override: Optional[int] = Field(default=None)

    # ========================================
    # UI/UX設定
    # ========================================
    # 事業部門の呼称（業種によって変える：「事業部門」「店舗」「ブランド」等）
    business_unit_label: str = Field(default="事業部門")
    # ダッシュボードに表示するウェルカムメッセージ
    welcome_message: Optional[str] = Field(default=None)
    # フッターに表示するコピーライト
    footer_text: Optional[str] = Field(default=None)

    # ========================================
    # 機能フラグ
    # ========================================
    # AI機能を有効にするか
    feature_ai_enabled: bool = Field(default=True)
    # ナレッジベース機能を有効にするか
    feature_knowledge_enabled: bool = Field(default=True)
    # Issue/Insight機能を有効にするか
    feature_insights_enabled: bool = Field(default=True)
    # 日報機能を有効にするか
    feature_daily_log_enabled: bool = Field(default=True)

    # ========================================
    # タイムスタンプ
    # ========================================
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    tenant: Optional["Tenant"] = Relationship(back_populates="settings")


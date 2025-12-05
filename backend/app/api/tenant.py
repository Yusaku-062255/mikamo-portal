"""
テナント設定API

テナントごとのブランド設定、AIポリシー、機能フラグを取得・更新するエンドポイント。
SaaS展開時に各テナントが独自の設定を持てるようにする。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_session
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.tenant import Tenant, TenantSettings, AiTierPolicy

router = APIRouter(prefix="/api/tenant", tags=["tenant"])


# ========================================
# レスポンススキーマ
# ========================================

class TenantSettingsPublic(BaseModel):
    """公開用テナント設定（未認証でも取得可能な情報）"""
    tenant_name: str
    display_name: str
    logo_url: Optional[str]
    primary_color: str
    secondary_color: str
    business_unit_label: str
    welcome_message: Optional[str]
    footer_text: Optional[str]


class TenantSettingsFull(TenantSettingsPublic):
    """認証済みユーザー向けの完全なテナント設定"""
    # AI設定
    ai_tier_policy: AiTierPolicy
    ai_company_context: str
    ai_max_tokens_override: Optional[int]

    # 機能フラグ
    feature_ai_enabled: bool
    feature_knowledge_enabled: bool
    feature_insights_enabled: bool
    feature_daily_log_enabled: bool


class TenantSettingsUpdate(BaseModel):
    """テナント設定更新用スキーマ（管理者のみ）"""
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    ai_tier_policy: Optional[AiTierPolicy] = None
    ai_company_context: Optional[str] = None
    ai_max_tokens_override: Optional[int] = None
    business_unit_label: Optional[str] = None
    welcome_message: Optional[str] = None
    footer_text: Optional[str] = None
    feature_ai_enabled: Optional[bool] = None
    feature_knowledge_enabled: Optional[bool] = None
    feature_insights_enabled: Optional[bool] = None
    feature_daily_log_enabled: Optional[bool] = None


# ========================================
# ヘルパー関数
# ========================================

def get_or_create_tenant_settings(session: Session, tenant: Tenant) -> TenantSettings:
    """
    テナント設定を取得。存在しない場合はデフォルト値で作成。
    """
    statement = select(TenantSettings).where(TenantSettings.tenant_id == tenant.id)
    settings = session.exec(statement).first()

    if settings is None:
        # デフォルト設定を作成
        settings = TenantSettings(
            tenant_id=tenant.id,
            ai_company_context=f"{tenant.display_name}の従業員向けAIアシスタントです。"
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)

    return settings


# ========================================
# エンドポイント
# ========================================

@router.get("/settings/public", response_model=TenantSettingsPublic)
async def get_public_settings(
    tenant_name: str = "mikamo",
    session: Session = Depends(get_session)
):
    """
    公開用テナント設定を取得（未認証でもアクセス可能）

    ログイン画面でロゴやブランドカラーを表示するために使用。
    """
    statement = select(Tenant).where(Tenant.name == tenant_name)
    tenant = session.exec(statement).first()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )

    settings = get_or_create_tenant_settings(session, tenant)

    return TenantSettingsPublic(
        tenant_name=tenant.name,
        display_name=tenant.display_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        business_unit_label=settings.business_unit_label,
        welcome_message=settings.welcome_message,
        footer_text=settings.footer_text
    )


@router.get("/settings", response_model=TenantSettingsFull)
async def get_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    現在のユーザーのテナント設定を取得（認証必須）

    AI設定や機能フラグを含む完全な設定を返す。
    """
    # ユーザーのテナントを取得
    tenant = session.get(Tenant, current_user.tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )

    settings = get_or_create_tenant_settings(session, tenant)

    return TenantSettingsFull(
        tenant_name=tenant.name,
        display_name=tenant.display_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        business_unit_label=settings.business_unit_label,
        welcome_message=settings.welcome_message,
        footer_text=settings.footer_text,
        ai_tier_policy=settings.ai_tier_policy,
        ai_company_context=settings.ai_company_context,
        ai_max_tokens_override=settings.ai_max_tokens_override,
        feature_ai_enabled=settings.feature_ai_enabled,
        feature_knowledge_enabled=settings.feature_knowledge_enabled,
        feature_insights_enabled=settings.feature_insights_enabled,
        feature_daily_log_enabled=settings.feature_daily_log_enabled
    )


@router.patch("/settings", response_model=TenantSettingsFull)
async def update_settings(
    update_data: TenantSettingsUpdate,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    テナント設定を更新（管理者のみ）

    ブランド設定、AIポリシー、機能フラグを更新可能。
    """
    tenant = session.get(Tenant, current_user.tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )

    settings = get_or_create_tenant_settings(session, tenant)

    # 更新データを適用
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    session.add(settings)
    session.commit()
    session.refresh(settings)

    return TenantSettingsFull(
        tenant_name=tenant.name,
        display_name=tenant.display_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        business_unit_label=settings.business_unit_label,
        welcome_message=settings.welcome_message,
        footer_text=settings.footer_text,
        ai_tier_policy=settings.ai_tier_policy,
        ai_company_context=settings.ai_company_context,
        ai_max_tokens_override=settings.ai_max_tokens_override,
        feature_ai_enabled=settings.feature_ai_enabled,
        feature_knowledge_enabled=settings.feature_knowledge_enabled,
        feature_insights_enabled=settings.feature_insights_enabled,
        feature_daily_log_enabled=settings.feature_daily_log_enabled
    )

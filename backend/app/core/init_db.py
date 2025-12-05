"""
データベース初期化処理（マルチテナントSaaS対応）

アプリ起動時に以下を実行:
1. デフォルトテナントを自動作成（初回起動時のみ）
2. 事業部門（Department + BusinessUnit）を自動作成
3. 初期管理者ユーザーを自動作成（環境変数から読み込み）

【SaaS展開時の注意】
- TENANT_NAME, TENANT_DISPLAY_NAME はデフォルトテナントの設定
- 新規テナントは管理APIまたは管理コンソールから追加
- 既存テナントのデータは init_database() では変更されない
"""
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, Department
from app.models.tenant import Tenant, TenantSettings, AiTierPolicy
from app.models.business_unit import BusinessUnit, BusinessUnitType
from typing import Optional


# ============================================================
# デフォルトテナント設定
# SaaS展開時: 環境変数 DEFAULT_TENANT_NAME, DEFAULT_TENANT_DISPLAY_NAME で上書き可能
# ============================================================
TENANT_NAME = getattr(settings, "DEFAULT_TENANT_NAME", "mikamo")
TENANT_DISPLAY_NAME = getattr(settings, "DEFAULT_TENANT_DISPLAY_NAME", "DXポータル")

# 事業部門の定義（既存のDepartment用 - 後方互換性）
DEPARTMENTS = [
    {"name": "ミカモ喫茶", "code": "cafe"},
    {"name": "カーコーティング（SOUP）", "code": "coating"},
    {"name": "中古車販売（Mnet）", "code": "mnet"},
    {"name": "ミカモ石油（三加茂SS / ENEOS）", "code": "gas"},
    {"name": "本部（経営・経理・DX全社統括）", "code": "head"},
]

# BusinessUnit定義（マルチテナント対応版）
BUSINESS_UNITS = [
    {
        "name": "ミカモ石油（三加茂SS / ENEOS）",
        "code": "gas",
        "type": BusinessUnitType.GAS_STATION,
        "description": "ガソリンスタンド事業"
    },
    {
        "name": "カーコーティング（SOUP）",
        "code": "coating",
        "type": BusinessUnitType.CAR_COATING,
        "description": "カーコーティング事業"
    },
    {
        "name": "中古車販売（Mnet）",
        "code": "mnet",
        "type": BusinessUnitType.USED_CAR,
        "description": "中古車販売事業"
    },
    {
        "name": "ミカモ喫茶",
        "code": "cafe",
        "type": BusinessUnitType.CAFE,
        "description": "飲食・カフェ事業"
    },
    {
        "name": "本部（経営・経理・DX全社統括）",
        "code": "head",
        "type": BusinessUnitType.HQ,
        "description": "経営・経理・DX全社統括"
    },
]


def ensure_departments(session: Session) -> None:
    """
    5つの事業部門が存在することを保証する
    
    既に存在する場合は何もしない（upsert的な動作）
    """
    for dept_data in DEPARTMENTS:
        statement = select(Department).where(Department.code == dept_data["code"])
        existing = session.exec(statement).first()
        
        if not existing:
            department = Department(
                name=dept_data["name"],
                code=dept_data["code"]
            )
            session.add(department)
            print(f"✅ 部門を作成しました: {dept_data['name']} ({dept_data['code']})")
        else:
            # 既存の部門名を更新（コードが一致する場合）
            if existing.name != dept_data["name"]:
                existing.name = dept_data["name"]
                session.add(existing)
                print(f"✅ 部門名を更新しました: {dept_data['name']} ({dept_data['code']})")
    
    session.commit()


def ensure_initial_admin(session: Session, tenant: Tenant) -> None:
    """
    初期管理者ユーザーを自動作成する
    
    環境変数から以下を読み込む:
    - INITIAL_ADMIN_EMAIL
    - INITIAL_ADMIN_PASSWORD
    - INITIAL_ADMIN_FULL_NAME
    
    既に role='admin' のユーザーが存在する場合は何もしない
    """
    # 既にadminユーザーが存在するかチェック
    statement = select(User).where(User.role == "admin")
    existing_admin = session.exec(statement).first()
    
    if existing_admin:
        print("ℹ️  既に管理者ユーザーが存在するため、初期管理者の自動作成をスキップします")
        return
    
    # 環境変数をチェック
    admin_email = getattr(settings, "INITIAL_ADMIN_EMAIL", None)
    admin_password = getattr(settings, "INITIAL_ADMIN_PASSWORD", None)
    admin_full_name = getattr(settings, "INITIAL_ADMIN_FULL_NAME", None)
    
    # 環境変数が設定されていない場合は管理者を作成しない（セキュリティ対策）
    # 本番環境では必ず Secret Manager から環境変数を設定すること
    if not admin_email or not admin_password:
        print("⚠️  INITIAL_ADMIN_EMAIL または INITIAL_ADMIN_PASSWORD が設定されていません")
        print("   初期管理者ユーザーの自動作成をスキップします")
        print("   本番環境では Secret Manager からこれらの環境変数を設定してください")
        return

    if not admin_full_name:
        admin_full_name = "管理者"
    
    # 本部（head）のBusinessUnitを取得
    statement = select(BusinessUnit).where(
        BusinessUnit.code == "head",
        BusinessUnit.tenant_id == tenant.id
    )
    head_business_unit = session.exec(statement).first()

    # 後方互換性のため、Departmentも取得
    statement = select(Department).where(Department.code == "head")
    head_department = session.exec(statement).first()

    if not head_business_unit:
        print("⚠️  本部（head）事業部門が見つかりません。先に事業部門を初期化してください")
        return

    if not head_department:
        print("⚠️  本部（head）部門が見つかりません。先に部門を初期化してください")
        return
    
    # 既に同じメールアドレスのユーザーが存在するかチェック
    statement = select(User).where(User.email == admin_email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        print(f"⚠️  メールアドレス {admin_email} のユーザーが既に存在します")
        return
    
    # 初期管理者ユーザーを作成
    hashed_password = get_password_hash(admin_password)
    admin_user = User(
        tenant_id=tenant.id,
        email=admin_email,
        hashed_password=hashed_password,
        full_name=admin_full_name,
        department_id=head_department.id,  # 後方互換性
        business_unit_id=head_business_unit.id,  # 新しいBusinessUnit参照
        role="admin",
        is_active=True
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    print(f"✅ 初期管理者ユーザーを作成しました: {admin_full_name} ({admin_email})")
    print(f"   ロール: admin, テナント: {tenant.display_name}, 事業部門: {head_business_unit.name}")


def ensure_tenant(session: Session) -> Tenant:
    """
    テナント（株式会社ミカモ）が存在することを保証する
    
    Returns:
        テナントオブジェクト
    """
    statement = select(Tenant).where(Tenant.name == TENANT_NAME)
    existing = session.exec(statement).first()
    
    if not existing:
        tenant = Tenant(
            name=TENANT_NAME,
            display_name=TENANT_DISPLAY_NAME
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        print(f"✅ テナントを作成しました: {TENANT_DISPLAY_NAME} ({TENANT_NAME})")
        return tenant
    else:
        print(f"ℹ️  テナントは既に存在します: {TENANT_DISPLAY_NAME} ({TENANT_NAME})")
        return existing


def ensure_tenant_settings(session: Session, tenant: Tenant) -> TenantSettings:
    """
    テナント設定が存在することを保証する

    デフォルト値で作成。テナント固有の設定は管理画面から後で変更可能。

    Args:
        session: データベースセッション
        tenant: テナントオブジェクト

    Returns:
        TenantSettingsオブジェクト
    """
    statement = select(TenantSettings).where(TenantSettings.tenant_id == tenant.id)
    existing = session.exec(statement).first()

    if not existing:
        # 汎用的なAIコンテキスト（テナント固有の情報は管理画面から設定）
        default_ai_context = f"""あなたは{tenant.display_name}の従業員向けAIアシスタントです。

従業員からの質問に対して、丁寧かつ的確に回答してください。
社内ナレッジベースの情報を参照しながら、業務改善や課題解決のサポートを行います。

わからないことは正直に「わかりません」と伝え、必要に応じて上長への確認を促してください。"""

        tenant_settings = TenantSettings(
            tenant_id=tenant.id,
            # ブランド設定
            logo_url=None,  # 将来的にロゴURLを設定可能
            primary_color="#3B82F6",  # Tailwind blue-500
            secondary_color="#1E40AF",  # Tailwind blue-800
            # AI設定
            ai_tier_policy=AiTierPolicy.ALL,  # 全ティア利用可能
            ai_company_context=default_ai_context,
            ai_max_tokens_override=None,  # デフォルトのトークン制限を使用
            # UI/UX設定
            business_unit_label="事業部門",
            welcome_message=f"ようこそ、{tenant.display_name}ポータルへ",
            footer_text=f"© {tenant.display_name}",
            # 機能フラグ（全機能有効）
            feature_ai_enabled=True,
            feature_knowledge_enabled=True,
            feature_insights_enabled=True,
            feature_daily_log_enabled=True,
        )
        session.add(tenant_settings)
        session.commit()
        session.refresh(tenant_settings)
        print(f"✅ テナント設定を作成しました: {tenant.display_name}")
        return tenant_settings
    else:
        print(f"ℹ️  テナント設定は既に存在します: {tenant.display_name}")
        return existing


def ensure_business_units(session: Session, tenant: Tenant) -> None:
    """
    5つの事業部門（BusinessUnit）が存在することを保証する
    
    Args:
        tenant: テナントオブジェクト
    """
    for bu_data in BUSINESS_UNITS:
        statement = select(BusinessUnit).where(
            BusinessUnit.code == bu_data["code"],
            BusinessUnit.tenant_id == tenant.id
        )
        existing = session.exec(statement).first()
        
        if not existing:
            business_unit = BusinessUnit(
                tenant_id=tenant.id,
                name=bu_data["name"],
                code=bu_data["code"],
                type=bu_data["type"],
                description=bu_data["description"]
            )
            session.add(business_unit)
            print(f"✅ 事業部門を作成しました: {bu_data['name']} ({bu_data['code']})")
        else:
            # 既存の事業部門名を更新（コードが一致する場合）
            if existing.name != bu_data["name"] or existing.type != bu_data["type"]:
                existing.name = bu_data["name"]
                existing.type = bu_data["type"]
                existing.description = bu_data["description"]
                session.add(existing)
                print(f"✅ 事業部門名を更新しました: {bu_data['name']} ({bu_data['code']})")
    
    session.commit()


def init_database() -> None:
    """
    データベース初期化処理のメイン関数
    
    アプリ起動時に呼び出される
    """
    with Session(engine) as session:
        # 1. テナントを初期化
        print("\n" + "=" * 60)
        print("🏢 データベース初期化: テナントの作成")
        print("=" * 60)
        tenant = ensure_tenant(session)
        
        # 2. テナント設定を初期化
        print("\n" + "=" * 60)
        print("⚙️  データベース初期化: テナント設定の作成")
        print("=" * 60)
        ensure_tenant_settings(session, tenant)

        # 3. 既存のDepartmentを初期化（後方互換性のため）
        print("\n" + "=" * 60)
        print("📋 データベース初期化: 部門（Department）の作成")
        print("=" * 60)
        ensure_departments(session)
        
        # 4. BusinessUnitを初期化（マルチテナント対応版）
        print("\n" + "=" * 60)
        print("📋 データベース初期化: 事業部門（BusinessUnit）の作成")
        print("=" * 60)
        ensure_business_units(session, tenant)
        
        # 5. 初期管理者ユーザーを作成
        print("\n" + "=" * 60)
        print("👤 データベース初期化: 初期管理者ユーザーの作成")
        print("=" * 60)
        ensure_initial_admin(session, tenant)
        
        print("\n" + "=" * 60)
        print("✅ データベース初期化が完了しました")
        print("=" * 60 + "\n")


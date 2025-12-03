"""
データベース初期化処理

アプリ起動時に以下を実行:
1. テナント（株式会社ミカモ）を自動作成
2. 5つの事業部門（Department + BusinessUnit）を自動作成
3. 初期管理者ユーザーを自動作成（環境変数から読み込み）
"""
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, Department
from app.models.tenant import Tenant
from app.models.business_unit import BusinessUnit, BusinessUnitType
from typing import Optional


# テナント定義（現時点では株式会社ミカモのみ）
TENANT_NAME = "mikamo"
TENANT_DISPLAY_NAME = "株式会社ミカモ"

# 5つの事業部門の定義（既存のDepartment用）
DEPARTMENTS = [
    {"name": "ミカモ喫茶", "code": "cafe"},
    {"name": "カーコーティング（SOUP）", "code": "coating"},
    {"name": "中古車販売", "code": "mnet"},
    {"name": "ミカモ石油（ガソリンスタンド）", "code": "gas"},
    {"name": "経営本陣（本社・経営）", "code": "head"},
]

# BusinessUnit定義（マルチテナント対応版）
BUSINESS_UNITS = [
    {
        "name": "ミカモ石油（ガソリンスタンド）",
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
        "name": "中古車販売",
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
        "name": "経営本陣（本社・経営）",
        "code": "head",
        "type": BusinessUnitType.HQ,
        "description": "本部（経営・経理・全社方針）"
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
    
    # デフォルト値（開発環境用・本番環境の初期セットアップ用）
    # 本番環境では Secret Manager から環境変数を設定することで上書き可能
    if not admin_email:
        admin_email = "info@mikamo.tokushima.jp"
    if not admin_password:
        admin_password = "mikamo1213"
    if not admin_full_name:
        admin_full_name = "管理者"
    
    # 経営本陣（head）のBusinessUnitを取得
    statement = select(BusinessUnit).where(
        BusinessUnit.code == "head",
        BusinessUnit.tenant_id == tenant.id
    )
    head_business_unit = session.exec(statement).first()
    
    # 後方互換性のため、Departmentも取得
    statement = select(Department).where(Department.code == "head")
    head_department = session.exec(statement).first()
    
    if not head_business_unit:
        print("⚠️  経営本陣（head）事業部門が見つかりません。先に事業部門を初期化してください")
        return
    
    if not head_department:
        print("⚠️  経営本陣（head）部門が見つかりません。先に部門を初期化してください")
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
        
        # 2. 既存のDepartmentを初期化（後方互換性のため）
        print("\n" + "=" * 60)
        print("📋 データベース初期化: 部門（Department）の作成")
        print("=" * 60)
        ensure_departments(session)
        
        # 3. BusinessUnitを初期化（マルチテナント対応版）
        print("\n" + "=" * 60)
        print("📋 データベース初期化: 事業部門（BusinessUnit）の作成")
        print("=" * 60)
        ensure_business_units(session, tenant)
        
        # 4. 初期管理者ユーザーを作成
        print("\n" + "=" * 60)
        print("👤 データベース初期化: 初期管理者ユーザーの作成")
        print("=" * 60)
        ensure_initial_admin(session, tenant)
        
        print("\n" + "=" * 60)
        print("✅ データベース初期化が完了しました")
        print("=" * 60 + "\n")


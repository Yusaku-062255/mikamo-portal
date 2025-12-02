"""
データベース初期化処理

アプリ起動時に以下を実行:
1. 5つの事業部門（Department）を自動作成
2. 初期管理者ユーザーを自動作成（環境変数から読み込み）
"""
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, Department
from typing import Optional


# 5つの事業部門の定義
DEPARTMENTS = [
    {"name": "ミカモ喫茶", "code": "cafe"},
    {"name": "カーコーティング（SOUP）", "code": "coating"},
    {"name": "中古車販売", "code": "mnet"},
    {"name": "ミカモ石油（ガソリンスタンド）", "code": "gas"},
    {"name": "経営本陣（本社・経営）", "code": "head"},
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


def ensure_initial_admin(session: Session) -> None:
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
    
    # 経営本陣（head）の部門IDを取得
    statement = select(Department).where(Department.code == "head")
    head_department = session.exec(statement).first()
    
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
        email=admin_email,
        hashed_password=hashed_password,
        full_name=admin_full_name,
        department_id=head_department.id,
        role="admin",
        is_active=True
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    print(f"✅ 初期管理者ユーザーを作成しました: {admin_full_name} ({admin_email})")
    print(f"   ロール: admin, 部門: {head_department.name}")


def init_database() -> None:
    """
    データベース初期化処理のメイン関数
    
    アプリ起動時に呼び出される
    """
    with Session(engine) as session:
        # 1. 部門を初期化
        print("\n" + "=" * 60)
        print("📋 データベース初期化: 部門の作成")
        print("=" * 60)
        ensure_departments(session)
        
        # 2. 初期管理者ユーザーを作成
        print("\n" + "=" * 60)
        print("👤 データベース初期化: 初期管理者ユーザーの作成")
        print("=" * 60)
        ensure_initial_admin(session)
        
        print("\n" + "=" * 60)
        print("✅ データベース初期化が完了しました")
        print("=" * 60 + "\n")


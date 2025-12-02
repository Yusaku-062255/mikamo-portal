"""
初期管理者ユーザーを手動で作成するスクリプト

既にデータベースが存在する場合に、管理者ユーザーを手動で作成するために使用します。
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User, Department


def create_admin_user(email: str, password: str, full_name: str = "管理者") -> None:
    """
    管理者ユーザーを作成
    
    Args:
        email: メールアドレス
        password: パスワード
        full_name: 氏名（デフォルト: "管理者"）
    """
    with Session(engine) as session:
        # 既に同じメールアドレスのユーザーが存在するかチェック
        statement = select(User).where(User.email == email)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            print(f"⚠️  メールアドレス {email} のユーザーが既に存在します")
            if existing_user.role == "admin":
                print(f"   既に管理者権限が付与されています（ID: {existing_user.id}）")
            else:
                # 既存ユーザーを管理者に昇格
                existing_user.role = "admin"
                existing_user.is_active = True
                session.add(existing_user)
                session.commit()
                print(f"✅ 既存ユーザーを管理者に昇格しました（ID: {existing_user.id}）")
            return
        
        # 経営本陣（head）の部門IDを取得
        statement = select(Department).where(Department.code == "head")
        head_department = session.exec(statement).first()
        
        if not head_department:
            print("⚠️  経営本陣（head）部門が見つかりません。先に部門を初期化してください")
            print("   アプリを起動すると自動的に部門が作成されます")
            return
        
        # 管理者ユーザーを作成
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            department_id=head_department.id,
            role="admin",
            is_active=True
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print(f"✅ 管理者ユーザーを作成しました:")
        print(f"   ID: {admin_user.id}")
        print(f"   メールアドレス: {email}")
        print(f"   氏名: {full_name}")
        print(f"   ロール: admin")
        print(f"   部門: {head_department.name}")


if __name__ == "__main__":
    # デフォルト値（環境変数から読み込むか、引数で指定）
    import argparse
    
    parser = argparse.ArgumentParser(description="管理者ユーザーを作成")
    parser.add_argument("--email", default="info@mikamo.tokushima.jp", help="メールアドレス")
    parser.add_argument("--password", default="mikamo1213", help="パスワード")
    parser.add_argument("--full-name", default="管理者", help="氏名")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("管理者ユーザー作成スクリプト")
    print("=" * 60)
    print()
    
    create_admin_user(args.email, args.password, args.full_name)
    
    print()
    print("=" * 60)
    print("完了")
    print("=" * 60)


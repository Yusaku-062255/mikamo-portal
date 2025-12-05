"""
デモ用スタッフユーザーを作成するスクリプト

Idempotent（べき等）に設計されており、同じメールアドレスのユーザーが存在する場合は何もしません。
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User, Department
from app.models.tenant import Tenant


def create_demo_staff_user(
    email: str,
    password: str,
    full_name: str = "Mikamo Demo Staff"
) -> None:
    """
    デモ用スタッフユーザーを作成（idempotent）

    Args:
        email: メールアドレス
        password: パスワード
        full_name: 氏名
    """
    with Session(engine) as session:
        # 既に同じメールアドレスのユーザーが存在するかチェック
        statement = select(User).where(User.email == email)
        existing_user = session.exec(statement).first()

        if existing_user:
            print(f"INFO: メールアドレス {email} のユーザーが既に存在します")
            print(f"   ユーザーID: {existing_user.id}")
            print(f"   ロール: {existing_user.role}")
            print(f"   状態: {'アクティブ' if existing_user.is_active else '無効'}")
            print("\n何もしません（idempotent）")
            return

        # mikamoテナントを取得
        statement = select(Tenant).where(Tenant.name == "mikamo")
        tenant = session.exec(statement).first()

        if not tenant:
            print("ERROR: mikamoテナントが見つかりません")
            print("   アプリを起動してテナントを初期化してください")
            return

        # スタッフ用の部門を取得（ミカモ喫茶をデフォルトに）
        statement = select(Department).where(Department.code == "cafe")
        department = session.exec(statement).first()

        if not department:
            # フォールバック: 最初に見つかった部門を使用
            statement = select(Department)
            department = session.exec(statement).first()

        if not department:
            print("ERROR: 部門が見つかりません")
            print("   アプリを起動して部門を初期化してください")
            return

        # スタッフユーザーを作成
        hashed_password = get_password_hash(password)
        staff_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            department_id=department.id,
            tenant_id=tenant.id,
            role="staff",  # 一般従業員ロール
            is_active=True
        )
        session.add(staff_user)
        session.commit()
        session.refresh(staff_user)

        print(f"SUCCESS: デモ用スタッフユーザーを作成しました:")
        print(f"   ユーザーID: {staff_user.id}")
        print(f"   メールアドレス: {email}")
        print(f"   氏名: {full_name}")
        print(f"   ロール: staff")
        print(f"   部門: {department.name}")
        print(f"   テナント: {tenant.name}")
        print()
        print("WARNING: 本番運用前にこのテストアカウントのパスワードを変更することを推奨します")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="デモ用スタッフユーザーを作成")
    parser.add_argument("--email", required=True, help="メールアドレス（必須）")
    parser.add_argument("--password", required=True, help="パスワード（必須）")
    parser.add_argument("--full-name", default="Mikamo Demo Staff", help="氏名")

    args = parser.parse_args()

    print("=" * 60)
    print("デモ用スタッフユーザー作成スクリプト")
    print("=" * 60)
    print()

    create_demo_staff_user(args.email, args.password, args.full_name)

    print()
    print("=" * 60)
    print("完了")
    print("=" * 60)

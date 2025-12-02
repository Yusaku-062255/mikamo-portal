"""
初期データ作成スクリプト
部署と初期ユーザーを作成します。
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.core.security import get_password_hash
from app.models.user import User, Department


def create_initial_data():
    """初期データを作成"""
    # データベーステーブルを作成
    init_db()

    with Session(engine) as session:
        # 部署を作成
        departments_data = [
            {"name": "ガソリンスタンド", "code": "gas"},
            {"name": "コーティング", "code": "coating"},
            {"name": "カフェ", "code": "cafe"},
            {"name": "本部", "code": "head"},
            {"name": "Mnet", "code": "mnet"},
        ]

        for dept_data in departments_data:
            statement = select(Department).where(Department.code == dept_data["code"])
            existing = session.exec(statement).first()
            if not existing:
                department = Department(**dept_data)
                session.add(department)
                print(f"✓ 部署を作成: {dept_data['name']} ({dept_data['code']})")
            else:
                print(f"→ 部署は既に存在: {dept_data['name']} ({dept_data['code']})")

        session.commit()

        # 初期ユーザーを作成（テスト用）
        # 本番環境では適切なユーザー情報に変更してください
        test_user_email = "test@mikamo.co.jp"
        statement = select(User).where(User.email == test_user_email)
        existing_user = session.exec(statement).first()

        if not existing_user:
            # ガソリンスタンド部署を取得
            statement = select(Department).where(Department.code == "gas")
            gas_dept = session.exec(statement).first()

            if gas_dept:
                user = User(
                    email=test_user_email,
                    hashed_password=get_password_hash("test1234"),  # 本番環境では変更必須
                    full_name="テストユーザー",
                    department_id=gas_dept.id,
                    role="staff",
                )
                session.add(user)
                session.commit()
                print(f"✓ テストユーザーを作成: {test_user_email} (パスワード: test1234)")
            else:
                print("⚠ ガソリンスタンド部署が見つかりません")
        else:
            print(f"→ ユーザーは既に存在: {test_user_email}")

    print("\n初期データの作成が完了しました！")


if __name__ == "__main__":
    create_initial_data()


"""
データベース接続とセッション管理

【重要】本番環境（Cloud Run）では、DATABASE_URL 環境変数が必須です。
Secret Manager から DATABASE_URL を注入してください。

ローカル開発環境では、USE_LOCAL_DB=true を設定して POSTGRES_* 環境変数を使用できます。
"""
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# データベースエンジンを作成
# settings.database_url は DATABASE_URL 環境変数を優先し、
# 未設定の場合は USE_LOCAL_DB=true の場合のみローカル設定を使用
# Cloud Run では DATABASE_URL が未設定の場合、ValueError が発生する
engine = create_engine(settings.database_url, echo=True)


def init_db():
    """データベーステーブルを作成"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """データベースセッションを取得"""
    with Session(engine) as session:
        yield session


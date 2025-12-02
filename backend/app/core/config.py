from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    # 【重要】本番環境（Cloud Run）では DATABASE_URL 環境変数（Secret Manager経由）が必須
    # ローカル開発環境では USE_LOCAL_DB=true を設定して、POSTGRES_* 環境変数を使用可能
    DATABASE_URL: Optional[str] = None
    
    # ローカル開発環境用の設定（USE_LOCAL_DB=true の場合のみ使用）
    # Cloud Run では使用しない（DATABASE_URL を必ず設定すること）
    USE_LOCAL_DB: bool = False  # ローカル開発時のみ true に設定
    POSTGRES_USER: str = "mikamo_user"
    POSTGRES_PASSWORD: str = "mikamo_password"
    POSTGRES_DB: str = "mikamo_portal"
    POSTGRES_HOST: str = "db"  # docker-compose のサービス名
    POSTGRES_PORT: int = 5432
    
    # Cloud SQL接続用（本番環境）
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None  # 例: "project:region:instance"
    USE_CLOUD_SQL_PROXY: bool = False

    # Security
    # 本番環境では JWT_SECRET_KEY 環境変数（Secret Manager経由）を優先
    JWT_SECRET_KEY: Optional[str] = None
    SECRET_KEY: str = "your-secret-key-change-in-production"  # ローカル開発用のデフォルト
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    @property
    def secret_key(self) -> str:
        """JWT秘密鍵を取得（JWT_SECRET_KEYが設定されていれば優先）"""
        return self.JWT_SECRET_KEY if self.JWT_SECRET_KEY else self.SECRET_KEY

    # CORS
    # 環境変数 BACKEND_CORS_ORIGINS が設定されている場合はそれを使用
    # カンマ区切りで複数指定可能、未設定時はデフォルト値を使用
    BACKEND_CORS_ORIGINS: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS許可オリジンを取得"""
        if self.BACKEND_CORS_ORIGINS:
            # カンマ区切りをリストに変換
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # Cloud Run (環境変数から取得、デフォルトは8080)
    PORT: int = 8080
    
    # OpenAI API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # GPT-4o-miniを使用

    @property
    def database_url(self) -> str:
        """
        データベース接続URLを生成
        
        【優先順位】
        1. DATABASE_URL 環境変数（本番環境では必須）
        2. USE_LOCAL_DB=true の場合のみ、POSTGRES_* 環境変数から構築
        
        Cloud Run では DATABASE_URL が未設定の場合、エラーを発生させる
        """
        # 最優先: DATABASE_URL 環境変数（Secret Manager経由で注入される）
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # ローカル開発環境用のフォールバック（USE_LOCAL_DB=true の場合のみ許可）
        if self.USE_LOCAL_DB:
            # Cloud SQL Proxyを使用する場合
            if self.USE_CLOUD_SQL_PROXY and self.CLOUD_SQL_CONNECTION_NAME:
                # Cloud SQL Proxy経由（ローカルホスト経由）
                return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@127.0.0.1:5432/{self.POSTGRES_DB}"
            # 通常の接続（docker-compose のローカルDB）
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # 本番環境で DATABASE_URL が未設定の場合はエラー
        import os
        env_name = os.getenv("ENVIRONMENT", "production")
        if env_name in ["production", "prod"] or os.getenv("K_SERVICE"):  # K_SERVICE は Cloud Run の環境変数
            raise ValueError(
                "DATABASE_URL 環境変数が設定されていません。"
                "Cloud Run では Secret Manager から DATABASE_URL を注入してください。"
            )
        
        # その他の環境でも警告を出す（開発環境の可能性があるためエラーにはしない）
        import warnings
        warnings.warn(
            "DATABASE_URL が未設定です。USE_LOCAL_DB=true を設定するか、"
            "DATABASE_URL 環境変数を設定してください。",
            UserWarning
        )
        # 警告のみで、ローカル開発用のデフォルトを返す（後方互換性のため）
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    # 【重要】本番環境（Cloud Run）では DATABASE_URL 環境変数（Secret Manager経由）が必須
    # ローカル開発環境では USE_LOCAL_DB=true を設定して、POSTGRES_* 環境変数を使用可能
    DATABASE_URL: Optional[str] = None
    
    # ローカル開発環境用の設定（USE_LOCAL_DB=true の場合のみ使用）
    # Cloud Run では使用しない（DATABASE_URL を必ず設定すること）
    # 【セキュリティ注意】これらの値は .env ファイルで必ず上書きすること
    USE_LOCAL_DB: bool = False  # ローカル開発時のみ true に設定
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
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
    
    # ============================================
    # Anthropic (Claude) API設定
    # ============================================
    # 本番環境では Secret Manager 経由で設定（Secret名: MIKAMO_ANTHROPIC_KEY）
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_API_BASE_URL: Optional[str] = None  # デフォルト: https://api.anthropic.com/v1/messages

    # ============================================
    # 3段階モデルティア設定（Anthropic Claude）
    # ============================================
    # 【BASIC】シフト管理、ログ要約など「軽めの業務オペレーション」用
    # 用途: shift_planning, log_summary, simple_task
    # 推奨: claude-3-haiku-20240307（最も安価・高速）
    ANTHROPIC_MODEL_BASIC: Optional[str] = None
    ANTHROPIC_MAX_TOKENS_BASIC: int = 500
    ANTHROPIC_TEMPERATURE_BASIC: float = 0.3

    # 【STANDARD】従業員Q&A、ナレッジ検索＋回答など「ある程度ちゃんと考える」用
    # 用途: staff_qa, knowledge_search, customer_support
    # 推奨: claude-3-haiku-20240307 または claude-3-5-sonnet-20241022
    ANTHROPIC_MODEL_STANDARD: Optional[str] = None
    ANTHROPIC_MAX_TOKENS_STANDARD: int = 1000
    ANTHROPIC_TEMPERATURE_STANDARD: float = 0.5

    # 【PREMIUM】経営判断支援、DXレポート分析など「精度最優先の重めタスク」用
    # 用途: management_decision, dx_report, strategic_planning
    # 推奨: claude-3-5-sonnet-20241022 または claude-3-opus-20240229
    ANTHROPIC_MODEL_PREMIUM: Optional[str] = None
    ANTHROPIC_MAX_TOKENS_PREMIUM: int = 4000
    ANTHROPIC_TEMPERATURE_PREMIUM: float = 0.7

    # ============================================
    # 後方互換性のための設定（非推奨・将来削除予定）
    # ============================================
    AI_PROVIDER: str = "anthropic"  # デフォルトをAnthropicに変更
    AI_API_KEY: Optional[str] = None
    AI_API_BASE_URL: Optional[str] = None
    AI_MODEL: str = "gpt-4o-mini"

    # スタッフQA用（後方互換性、新設定を推奨）
    AI_PROVIDER_STAFF: str = "anthropic"
    AI_MODEL_STAFF: Optional[str] = None  # 未設定の場合はANTHROPIC_MODEL_STANDARDを使用
    AI_MAX_TOKENS_STAFF: int = 1000
    AI_TEMPERATURE_STAFF: float = 0.5

    # OpenAI API（後方互換性のため残す）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # 初期管理者ユーザー（アプリ起動時に自動作成）
    # 本番環境では Secret Manager から注入することを推奨
    INITIAL_ADMIN_EMAIL: Optional[str] = None
    INITIAL_ADMIN_PASSWORD: Optional[str] = None
    INITIAL_ADMIN_FULL_NAME: Optional[str] = None

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
            # POSTGRES_USER と POSTGRES_PASSWORD が設定されているかチェック
            if not self.POSTGRES_USER or not self.POSTGRES_PASSWORD:
                raise ValueError(
                    "USE_LOCAL_DB=true の場合、POSTGRES_USER と POSTGRES_PASSWORD 環境変数が必須です。"
                    ".env ファイルでこれらを設定してください。"
                )
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
        
        # その他の環境でもエラーを発生（セキュリティ対策）
        raise ValueError(
            "DATABASE_URL が未設定です。"
            "ローカル開発の場合は USE_LOCAL_DB=true を設定し、POSTGRES_USER と POSTGRES_PASSWORD を設定してください。"
            "本番環境の場合は DATABASE_URL 環境変数を Secret Manager から設定してください。"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


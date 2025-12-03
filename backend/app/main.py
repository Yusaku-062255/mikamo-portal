from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging
from app.core.middleware import (
    add_request_id,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler
)
from app.api import auth, daily_logs, tasks, ai_chat, admin, knowledge, portal, issues, insights, decisions
from app.core.init_db import init_database
from app.core.migrate_columns import run_migrations

# ロギングを初期化
setup_logging()

app = FastAPI(
    title="みかもポータル API",
    description="株式会社ミカモのポータルシステム API",
    version="0.2.0"
)

# ミドルウェア（リクエストID生成）
app.middleware("http")(add_request_id)

# 例外ハンドラー
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router, prefix="/api/auth", tags=["認証"])
app.include_router(daily_logs.router, prefix="/api/daily-logs", tags=["日次ログ"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["タスク"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["AI相談"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理者"])
app.include_router(portal.router, prefix="/api/portal", tags=["ポータル"])
app.include_router(issues.router, prefix="/api/issues", tags=["Issue"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insight"])
app.include_router(decisions.router, prefix="/api/decisions", tags=["Decision"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["ナレッジベース"])


@app.on_event("startup")
async def on_startup():
    """
    アプリ起動時にデータベーステーブルを自動作成し、初期データを投入
    
    【処理順序】
    1. SQLModel.metadata.create_all() でテーブルを自動作成
    2. init_database() で部門と初期管理者ユーザーを自動作成
    
    【重要】本番環境（Cloud Run）では、Alembicマイグレーションをスキップし、
    代わりにこの処理でテーブルを自動作成します。
    
    理由:
    - 本番DBが空の場合、Alembicのマイグレーション（ALTER TABLE）が失敗する
    - SQLModel.metadata.create_all() は既存テーブルがあっても安全に動作する
    - 空のDBでも必要な全テーブルが作成され、アプリが正常に起動する
    """
    try:
        # 1. すべてのSQLModelテーブルを自動作成
        # 既に存在するテーブルはスキップされ、存在しないテーブルのみ作成される
        SQLModel.metadata.create_all(engine)
        print("✅ データベーステーブルの自動作成が完了しました")

        # 2. 欠けているカラムを追加（既存テーブルへのマイグレーション）
        run_migrations()

        # 3. 部門と初期管理者ユーザーを自動作成
        # init_database() 内で以下を実行:
        # - 5つの事業部門（ミカモ喫茶、カーコーティング、中古車販売、ミカモ石油、経営本陣）を作成
        # - 環境変数から初期管理者ユーザーを作成（INITIAL_ADMIN_EMAIL 等が設定されている場合）
        init_database()
        
    except Exception as e:
        # テーブル作成に失敗してもアプリは起動を継続（ログで確認可能）
        print(f"⚠️  データベース初期化でエラーが発生しました: {e}")
        print("   アプリケーションは起動しますが、DB接続エラーが発生する可能性があります")


@app.get("/")
async def root():
    return {"message": "みかもポータル API v0.2"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


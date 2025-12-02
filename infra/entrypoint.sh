#!/bin/sh
# Cloud Run コンテナ起動スクリプト
# マイグレーション実行後、uvicorn を起動

# エラー時に即終了しないようにする（マイグレーション失敗時もアプリを起動するため）
set +e

# マイグレーション実行フラグ
# 【重要】本番環境（Cloud Run）ではデフォルトで false（マイグレーションをスキップ）
# 理由: 本番DBが空の場合、Alembicのマイグレーション（ALTER TABLE）が失敗するため
# 代わりに、アプリ起動時に SQLModel.metadata.create_all() でテーブルを自動作成
# ローカル開発環境や明示的に RUN_MIGRATIONS=true を設定した場合のみ実行
if [ -n "$K_SERVICE" ]; then
    # Cloud Run 環境（K_SERVICE 環境変数が存在）
    RUN_MIGRATIONS=${RUN_MIGRATIONS:-false}
else
    # ローカル開発環境
    RUN_MIGRATIONS=${RUN_MIGRATIONS:-true}
fi

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "============================================================"
    echo "Running DB migrations (Alembic)..."
    echo "============================================================"
    
    # DATABASE_URL が設定されているか確認
    if [ -z "$DATABASE_URL" ]; then
        echo "⚠️  警告: DATABASE_URL 環境変数が設定されていません"
        echo "   マイグレーションをスキップします"
    else
        # マイグレーション実行（失敗してもコンテナは落とさない）
        if alembic upgrade head; then
            echo "✅ マイグレーションが正常に完了しました"
        else
            echo "❌ マイグレーションが失敗しました"
            echo "   アプリケーションは起動しますが、DB接続エラーが発生する可能性があります"
            echo "   Cloud Run のログで DATABASE_URL の設定を確認してください"
        fi
    fi
else
    echo "⚠️  マイグレーションをスキップします（本番環境では SQLModel.metadata.create_all() でテーブルを自動作成）"
fi

echo ""
echo "============================================================"
echo "Starting application..."
echo "============================================================"

# Cloud Run は PORT 環境変数を自動的に設定する（通常は 8080）
# 未設定の場合はデフォルトで 8080 を使用
PORT="${PORT:-8080}"

echo "Starting FastAPI app on port ${PORT} ..."

# uvicorn を起動（PID 1 として exec で実行）
# Cloud Run のヘルスチェックは PORT 環境変数で指定されたポートで listen する必要がある
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT}"


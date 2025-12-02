# GCP（Google Cloud Platform）へのデプロイ手順

みかもポータル v0.1 を Google Cloud Platform の Cloud Run と Cloud SQL にデプロイする手順です。

## 📋 前提条件

- Google Cloud Platform アカウント
- `gcloud` CLI がインストール・設定済み
- Docker がインストール済み
- プロジェクトの GCP プロジェクト ID が決定済み

## 🏗️ アーキテクチャ

- **Backend**: Cloud Run（コンテナ）
- **Frontend**: Cloud Run（Nginx + 静的ファイル）
- **Database**: Cloud SQL for PostgreSQL

## 📝 デプロイ手順

### 1. GCP プロジェクトの設定

```bash
# GCP プロジェクトを設定
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Cloud SQL インスタンスの作成

```bash
# Cloud SQL インスタンスを作成
gcloud sql instances create mikamo-portal-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast1 \
  --root-password=YOUR_SECURE_PASSWORD

# データベースを作成
gcloud sql databases create mikamo_portal \
  --instance=mikamo-portal-db

# ユーザーを作成
gcloud sql users create mikamo_user \
  --instance=mikamo-portal-db \
  --password=YOUR_SECURE_PASSWORD
```

### 3. Cloud SQL 接続情報の取得

```bash
# 接続名を取得
gcloud sql instances describe mikamo-portal-db \
  --format="value(connectionName)"
```

この値（例: `project:region:instance`）を環境変数に設定します。

### 4. バックエンドのデプロイ

#### 4.1 環境変数の設定

`.env.production` ファイルを作成（または Cloud Run の環境変数として設定）：

```bash
POSTGRES_USER=mikamo_user
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
POSTGRES_DB=mikamo_portal
POSTGRES_HOST=/cloudsql/PROJECT:REGION:INSTANCE
CLOUD_SQL_CONNECTION_NAME=PROJECT:REGION:INSTANCE
USE_CLOUD_SQL_PROXY=false
SECRET_KEY=YOUR_SECRET_KEY_CHANGE_THIS
CORS_ORIGINS=https://your-frontend-domain.com
```

#### 4.2 イメージをビルド・プッシュ

```bash
# Artifact Registry リポジトリを作成（初回のみ）
gcloud artifacts repositories create mikamo-portal \
  --repository-format=docker \
  --location=asia-northeast1

# バックエンドイメージをビルド
docker build -f infra/Dockerfile.backend -t asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest .

# イメージをプッシュ
docker push asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest
```

#### 4.3 Cloud Run にデプロイ

```bash
gcloud run deploy mikamo-portal-backend \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest \
  --platform=managed \
  --region=asia-northeast1 \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION_NAME \
  --set-env-vars="POSTGRES_USER=mikamo_user,POSTGRES_PASSWORD=YOUR_PASSWORD,POSTGRES_DB=mikamo_portal,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME,USE_CLOUD_SQL_PROXY=false,SECRET_KEY=YOUR_SECRET_KEY,CORS_ORIGINS=https://your-frontend-domain.com"
```

### 5. フロントエンドのデプロイ

#### 5.1 環境変数の設定

フロントエンドのビルド時にバックエンドのURLを設定：

```bash
export VITE_API_BASE_URL=https://your-backend-url.run.app
```

#### 5.2 イメージをビルド・プッシュ

```bash
# フロントエンドをビルド（環境変数を設定）
cd frontend
VITE_API_BASE_URL=https://your-backend-url.run.app npm run build
cd ..

# フロントエンドイメージをビルド
docker build -f infra/Dockerfile.frontend -t asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest .

# イメージをプッシュ
docker push asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest
```

#### 5.3 Cloud Run にデプロイ

```bash
gcloud run deploy mikamo-portal-frontend \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest \
  --platform=managed \
  --region=asia-northeast1 \
  --allow-unauthenticated
```

### 6. データベースマイグレーションの実行

```bash
# Cloud Run の一時コンテナでマイグレーションを実行
gcloud run jobs create mikamo-portal-migrate \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest \
  --region=asia-northeast1 \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION_NAME \
  --set-env-vars="POSTGRES_USER=mikamo_user,POSTGRES_PASSWORD=YOUR_PASSWORD,POSTGRES_DB=mikamo_portal,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME,USE_CLOUD_SQL_PROXY=false" \
  --command="alembic" \
  --args="upgrade,head"

# ジョブを実行
gcloud run jobs execute mikamo-portal-migrate --region=asia-northeast1
```

### 7. 初期データの投入

```bash
# 初期データ投入用のジョブを作成・実行
gcloud run jobs create mikamo-portal-init-data \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest \
  --region=asia-northeast1 \
  --add-cloudsql-instances=$CLOUD_SQL_CONNECTION_NAME \
  --set-env-vars="POSTGRES_USER=mikamo_user,POSTGRES_PASSWORD=YOUR_PASSWORD,POSTGRES_DB=mikamo_portal,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME,USE_CLOUD_SQL_PROXY=false" \
  --command="python" \
  --args="scripts/init_data.py"

# ジョブを実行
gcloud run jobs execute mikamo-portal-init-data --region=asia-northeast1
```

## 🔒 セキュリティ設定

### カスタムドメインの設定（推奨）

```bash
# カスタムドメインをマッピング
gcloud run domain-mappings create \
  --service=mikamo-portal-frontend \
  --domain=portal.mikamo.co.jp \
  --region=asia-northeast1
```

### IAM の設定

本番環境では、Cloud Run サービスへのアクセスを制限することを推奨します。

## 📊 モニタリング

```bash
# ログを確認
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# メトリクスを確認
gcloud monitoring dashboards list
```

## 🔄 更新デプロイ

### バックエンドの更新

```bash
# イメージを再ビルド・プッシュ
docker build -f infra/Dockerfile.backend -t asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest .
docker push asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest

# Cloud Run を更新
gcloud run services update mikamo-portal-backend \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/backend:latest \
  --region=asia-northeast1
```

### フロントエンドの更新

```bash
# フロントエンドを再ビルド
cd frontend
VITE_API_BASE_URL=https://your-backend-url.run.app npm run build
cd ..

# イメージを再ビルド・プッシュ
docker build -f infra/Dockerfile.frontend -t asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest .
docker push asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest

# Cloud Run を更新
gcloud run services update mikamo-portal-frontend \
  --image=asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/mikamo-portal/frontend:latest \
  --region=asia-northeast1
```

## 💰 コスト見積もり

- Cloud Run: リクエスト数とCPU時間に応じて課金（無料枠あり）
- Cloud SQL: インスタンスサイズに応じて課金（db-f1-micro は約 $7/月）
- Artifact Registry: ストレージと転送に応じて課金

詳細は [GCP 料金計算機](https://cloud.google.com/products/calculator) を参照してください。

## 🐛 トラブルシューティング

### Cloud SQL 接続エラー

```bash
# Cloud SQL Proxy を使用してローカルから接続テスト
cloud-sql-proxy $CLOUD_SQL_CONNECTION_NAME
```

### ログの確認

```bash
# バックエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-backend" --limit=50

# フロントエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-frontend" --limit=50
```

## 📚 参考資料

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud SQL ドキュメント](https://cloud.google.com/sql/docs)
- [Artifact Registry ドキュメント](https://cloud.google.com/artifact-registry/docs)


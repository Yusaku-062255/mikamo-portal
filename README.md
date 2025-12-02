# みかもポータル v0.2

株式会社ミカモの変革を支えるDXポータルシステム。現場スタッフが毎日使いたくなる、モチベーション向上を重視した設計です。

**v0.2の新機能:**
- 🤖 **AI機能**: OpenAI API統合、部署別コンテキスト付きアドバイス
- 📊 **経営ダッシュボード**: 売上・客数トレンド、部署間比較グラフ
- 💬 **エンゲージメント機能**: いいね、マネージャーコメント
- 📝 **ロギング・エラーハンドリング**: JSON形式ログ、Error Boundary

## 🎯 プロジェクトの哲学

「入力業務」をスタッフの負担にするのではなく、**「自分の仕事が認められる場」「明日のヒントが得られる場」**に変えること。

## 🚀 技術スタック

### Backend
- Python 3.11+
- FastAPI
- SQLModel
- PostgreSQL
- Alembic
- OpenAI API (GPT-4o-mini)
- structlog (JSON形式ログ)

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Zustand (状態管理)
- Recharts (グラフ可視化)
- PWA対応（vite-plugin-pwa）

### Infrastructure
- Docker
- Docker Compose

## 📱 モバイルファースト設計

- **親指1本完結**: スマホ画面下半分ですべての主要操作が可能
- **巨大なボタン**: 誤タップを防ぐため、ボタンは大きく、余白を十分に取る
- **ポジティブ・フィードバック**: 保存完了時は労いのメッセージとアニメーション
- **視認性**: 屋外でも見えるよう、コントラスト比が高い配色

## 🚀 本番環境へのデプロイ（GCP Cloud Run）

このプロジェクトは **GCP Cloud Run** へデプロイする前提で設計されています。

### 前提条件

#### GCP 側の前提条件

**1. 必要なAPIの有効化**

以下のAPIを有効化してください：

```bash
export PROJECT_ID="your-gcp-project-id"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  --project=$PROJECT_ID
```

**2. Secret Manager にシークレットを登録**

```bash
# データベースURL（Cloud SQL接続文字列）
echo -n "postgresql://user:password@host/dbname" | \
  gcloud secrets create MIKAMO_DB_URL \
  --project=$PROJECT_ID \
  --data-file=-

# JWT秘密鍵（強力なランダム文字列を生成）
openssl rand -base64 32 | \
  gcloud secrets create MIKAMO_JWT_SECRET \
  --project=$PROJECT_ID \
  --data-file=-

# OpenAI APIキー（オプション、AI機能を使用する場合）
echo -n "sk-..." | \
  gcloud secrets create MIKAMO_OPENAI_KEY \
  --project=$PROJECT_ID \
  --data-file=-
```

**3. Cloud SQL インスタンスの作成（必要に応じて）**

```bash
# Cloud SQL インスタンスを作成
gcloud sql instances create mikamo-portal-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast1 \
  --root-password=YOUR_SECURE_PASSWORD \
  --project=$PROJECT_ID

# データベースを作成
gcloud sql databases create mikamo_portal \
  --instance=mikamo-portal-db \
  --project=$PROJECT_ID
```

**4. サービスアカウントへの権限付与**

Cloud Run のサービスアカウントに Secret Manager へのアクセス権限を付与：

```bash
# Cloud Run のデフォルトサービスアカウントを取得
export SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

# Secret Manager へのアクセス権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

#### ローカル環境側の前提条件

**1. gcloud CLI のインストールと認証**

```bash
# gcloud CLI がインストールされているか確認
gcloud --version

# 認証（初回のみ）
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID
```

**2. 依存パッケージのインストール**

```bash
# PyYAML をインストール（デプロイスクリプトで使用）
pip install pyyaml
```

### デプロイ方法

**1. 環境変数を設定**

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-northeast1"
```

**2. デプロイコマンドを実行**

```bash
python scripts/manage_deploy.py prod \
  --project-id "$PROJECT_ID" \
  --region "$REGION"
```

**3. デプロイ完了後の確認**

デプロイが成功すると、ターミナルに以下のような出力が表示されます：

```
============================================================
✅ デプロイが完了しました！
============================================================

📱 Deployed frontend URL: https://mikamo-portal-frontend-xxxxx-an.a.run.app
🔧 Backend URL: https://mikamo-portal-backend-xxxxx-an.a.run.app

このURLを従業員に共有してください。
（最初のURLは長いですが、Google公式の安全なURLです）
============================================================
```

**4. 動作確認**

- フロントエンドURLにブラウザやスマホからアクセス
- ログイン画面が表示されることを確認
- テストユーザーでログインして動作確認

### トラブルシューティング

#### Cloud Run のログを確認

```bash
# バックエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-backend" \
  --limit=50 \
  --project=$PROJECT_ID

# フロントエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-frontend" \
  --limit=50 \
  --project=$PROJECT_ID
```

#### 環境変数・シークレットの確認

```bash
# バックエンドサービスの設定を確認
gcloud run services describe mikamo-portal-backend \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format=yaml
```

#### PORT関連のエラー

Cloud Run は自動的に `PORT` 環境変数を設定します。コンテナ内で `PORT` 環境変数を参照しているか確認してください。

- バックエンド: `infra/entrypoint.sh` で `${PORT:-8080}` を使用
- フロントエンド: `infra/nginx-start.sh` で `${PORT:-8080}` を使用

### ロールバック

ロールバックが必要な場合は、**Cloud Run コンソールのリビジョン機能**を使用してください。

```bash
# 現在のリビジョンを確認
gcloud run revisions list \
  --service=mikamo-portal-frontend \
  --region=$REGION \
  --project=$PROJECT_ID

# 特定のリビジョンにトラフィックを100%割り当て
gcloud run services update-traffic mikamo-portal-frontend \
  --to-revisions=REVISION_NAME=100 \
  --region=$REGION \
  --project=$PROJECT_ID
```

または、[Cloud Run コンソール](https://console.cloud.google.com/run)からGUIで操作可能です。

### マイグレーション

マイグレーションは**コンテナ起動時に自動実行**されます（`infra/entrypoint.sh` で `alembic upgrade head` を実行）。

Cloud Run Jobs は使用しません。コンテナが正常に起動すれば、マイグレーションも完了しています。

### 前提条件

#### 1. GCPプロジェクトの準備とAPI有効化

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com
```

#### 2. Cloud SQL インスタンスの作成

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

# ユーザーを作成（必要に応じて）
gcloud sql users create mikamo_user \
  --instance=mikamo-portal-db \
  --password=YOUR_SECURE_PASSWORD
```

#### 3. Secret Manager にシークレットを登録

```bash
# データベースURL（Cloud SQL接続文字列）
echo -n "postgresql://mikamo_user:password@/mikamo_portal?host=/cloudsql/PROJECT:REGION:mikamo-portal-db" | \
  gcloud secrets create MIKAMO_DB_URL \
  --project=$PROJECT_ID \
  --data-file=-

# JWT秘密鍵（強力なランダム文字列を生成）
openssl rand -base64 32 | \
  gcloud secrets create MIKAMO_JWT_SECRET \
  --project=$PROJECT_ID \
  --data-file=-

# OpenAI APIキー（オプション、AI機能を使用する場合）
echo -n "sk-..." | \
  gcloud secrets create MIKAMO_OPENAI_KEY \
  --project=$PROJECT_ID \
  --data-file=-
```


### ロールバック

ロールバックが必要な場合は、**Cloud Run コンソールのリビジョン機能**を使用してください。

```bash
# 現在のリビジョンを確認
gcloud run revisions list \
  --service=mikamo-portal-frontend \
  --region=asia-northeast1 \
  --project=$PROJECT_ID

# 特定のリビジョンにトラフィックを100%割り当て
gcloud run services update-traffic mikamo-portal-frontend \
  --to-revisions=REVISION_NAME=100 \
  --region=asia-northeast1 \
  --project=$PROJECT_ID
```

または、[Cloud Run コンソール](https://console.cloud.google.com/run)からGUIで操作可能です。

### マイグレーション

マイグレーションは**コンテナ起動時に自動実行**されます（`infra/entrypoint.sh` で `alembic upgrade head` を実行）。

Cloud Run Jobs は使用しません。コンテナが正常に起動すれば、マイグレーションも完了しています。

### トラブルシューティング

#### Cloud Run のログを確認

```bash
# バックエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-backend" \
  --limit=50 \
  --project=$PROJECT_ID

# フロントエンドのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-frontend" \
  --limit=50 \
  --project=$PROJECT_ID
```

#### 環境変数・シークレットの確認

```bash
# バックエンドサービスの設定を確認
gcloud run services describe mikamo-portal-backend \
  --region=asia-northeast1 \
  --project=$PROJECT_ID \
  --format=yaml
```

#### PORT関連のエラー

Cloud Run は自動的に `PORT` 環境変数を設定します。コンテナ内で `PORT` 環境変数を参照しているか確認してください。

- バックエンド: `entrypoint.sh` で `${PORT:-8080}` を使用
- フロントエンド: `nginx-start.sh` で `${PORT:-8080}` を使用

## 🏗️ ローカル開発環境のセットアップ

### 前提条件
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose（PostgreSQL用）
- ポート 8000（Backend）、5173（Frontend）、5432（PostgreSQL）が空いていること

### 起動方法

#### 1. 環境変数を設定
```bash
cp .env.example .env
# .env ファイルを編集して必要な値を設定
```

#### 2. PostgreSQLデータベースを起動（Docker Compose）
```bash
docker-compose up -d
```

#### 3. バックエンドのセットアップ
```bash
cd backend

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# データベースマイグレーション実行
alembic upgrade head

# 初期データ作成（部署とテストユーザー）
python scripts/init_data.py

# バックエンドを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. フロントエンドのセットアップ（別ターミナル）
```bash
cd frontend

# 依存関係をインストール
npm install

# フロントエンドを起動
npm run dev
```

#### 5. アクセス
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**テストユーザー情報:**
- メールアドレス: `test@mikamo.co.jp`
- パスワード: `test1234`

## 📱 スマホでの動作確認方法

### 開発環境での確認

1. **同一ネットワーク内のスマホからアクセス**
   - PCのIPアドレスを確認: `ifconfig` (Mac/Linux) または `ipconfig` (Windows)
   - スマホのブラウザで `http://<PCのIPアドレス>:5173` にアクセス

2. **Chrome DevToolsのモバイルエミュレーション**
   - Chromeで `http://localhost:5173` を開く
   - F12でDevToolsを開く
   - デバイスツールバー（Ctrl+Shift+M / Cmd+Shift+M）でモバイル表示に切り替え
   - デバイスを「iPhone 12 Pro」や「Pixel 5」などに設定

3. **PWAとしてインストール**
   - スマホのブラウザでアクセス
   - ブラウザのメニューから「ホーム画面に追加」を選択
   - アプリアイコンから起動可能に

### 本番環境での確認

本番環境では、HTTPSが必要です（PWAの要件）。適切なドメインとSSL証明書を設定してください。

## 📂 プロジェクト構成

```
mikamo_portal/
├── backend/              # FastAPI バックエンド
│   ├── app/
│   │   ├── models/       # SQLModel モデル
│   │   ├── api/          # API エンドポイント
│   │   │   └── deps.py   # 認証・権限チェック依存関係
│   │   ├── core/         # 設定、認証など
│   │   ├── services/     # ビジネスロジック（AIサービス等）
│   │   └── main.py       # FastAPI アプリケーション
│   ├── alembic/          # データベースマイグレーション
│   ├── scripts/          # 初期データ作成スクリプト
│   └── requirements.txt
├── frontend/             # React フロントエンド
│   ├── src/
│   │   ├── components/   # React コンポーネント
│   │   ├── pages/        # ページコンポーネント
│   │   ├── stores/       # Zustand ストア
│   │   └── utils/        # ユーティリティ
│   ├── public/           # 静的ファイル（PWA用アイコン等）
│   └── package.json
├── infra/                # デプロイ関連ファイル
│   ├── Dockerfile.backend    # Cloud Run用バックエンドDockerfile
│   ├── Dockerfile.frontend   # Cloud Run用フロントエンドDockerfile
│   ├── nginx.conf        # Nginx設定
│   └── nginx-start.sh    # Nginx起動スクリプト
├── docker-compose.yml    # ローカル開発用（PostgreSQLのみ）
├── .env.example          # 環境変数テンプレート
└── README.md
```

## 🔐 認証

初期ユーザーは `scripts/init_data.py` を実行して作成してください。

```bash
docker-compose exec backend python scripts/init_data.py
```

このスクリプトは以下を作成します：
- 部署（ガソリンスタンド、コーティング、カフェ、本部、Mnet）
- テストユーザー（test@mikamo.co.jp / test1234）

本番環境では、適切なユーザー情報に変更してください。

## 📊 主要機能

### 一般スタッフ向け
- **ダッシュボード**: 挨拶、チームの状況、今週の頑張り表示
- **今日の振り返り**: 天気、KPI、定性データの入力
- **AI相談**: 部署別コンテキスト付きアドバイス（OpenAI API統合）
- **エンゲージメント**: いいね機能、マネージャーからのコメント表示

### マネージャー・経営向け
- **経営ダッシュボード**: 売上・客数トレンドグラフ（14日間）
- **部署間比較**: 全部署の今日の状況を可視化
- **マネージャーコメント**: スタッフへの承認＋次の一歩のヒント

### 技術的機能
- **ロギング**: JSON形式ログ、リクエストID追跡
- **エラーハンドリング**: Error Boundary、統一されたエラー応答

## 🎨 デザインシステム

- **メインカラー**: ミカモブルー
- **アクセントカラー**: オレンジ
- **背景**: 白
- **フォント**: システムフォント（読みやすさ重視）

## 📝 開発ガイドライン

- モバイルファーストで設計
- すべての主要操作は画面下半分で完結
- ボタンは最低48px×48px以上
- エラーではなく、ポジティブなフィードバックを優先
- 音声入力にも対応できるよう、テキスト入力欄は大きめに

## 🤝 コントリビューション

このプロジェクトは株式会社ミカモの内部プロジェクトです。

## 🎨 PWAアイコンの設定

PWA機能を完全に有効にするには、以下のアイコンファイルを `frontend/public/` に配置してください：

- `pwa-192x192.png` (192x192ピクセル)
- `pwa-512x512.png` (512x512ピクセル)

これらのアイコンは、スマホのホーム画面に追加された際に表示されます。

## 🔧 トラブルシューティング

### データベース接続エラー
```bash
# データベースコンテナの状態を確認
docker-compose ps

# ログを確認
docker-compose logs db
```

### フロントエンドが起動しない
```bash
cd frontend
# 依存関係を再インストール
npm install
# node_modulesを削除して再インストール
rm -rf node_modules package-lock.json
npm install
```

### マイグレーションエラー
```bash
cd backend
# マイグレーションをリセット（開発環境のみ）
alembic downgrade base
alembic upgrade head
```

### データベース接続エラー
```bash
# PostgreSQLコンテナの状態を確認
docker-compose ps

# ログを確認
docker-compose logs db

# コンテナを再起動
docker-compose restart db
```

## 📚 ドキュメント

### DX関連ドキュメント

- **DXレンズプロンプト** (`docs/DX_LENS_PROMPT.md`): Cursor用のDX視点レビュープロンプト
- **月次DXふりかえりプロンプト** (`docs/MONTHLY_DX_REVIEW_PROMPT.md`): 月1でブレジンに投げる用のプロンプト
- **v0.2機能ガイド** (`docs/V0.2_FEATURES.md`): v0.2の新機能詳細

### AI機能について

v0.2から、AI機能は「DX参謀モード」にアップグレードされました。

- **5つのセクション構造**: 状況理解 → すぐできる一手 → 小さな実験 → 水平思考 → リスク
- **水平思考**: 他事業との連携アイデアを自動提案
- **小さな実験**: 1〜2週間で試せる施策を具体的に提案

詳細は `docs/V0.2_FEATURES.md` を参照してください。

## 📄 ライセンス

プロプライエタリ


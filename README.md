# みかもポータル v0.2

株式会社ミカモ専用の社内SaaS「ミカモポータル」。5つの事業部門を横断して業務情報を整理し、社内AIアシスタント＋ナレッジベースを組み込んだ、ミカモグループ専用のポータルシステムです。

## 📋 ミカモポータルとは

**ミカモポータル**は、株式会社ミカモの5つの事業部門（ミカモ石油、カーコーティング事業SOUP、中古車販売、ミカモ喫茶、本部）をまとめて扱う社内SaaSです。

### 主な機能

1. **部門別ポータル画面**
   - `/portal/hq` - 本部ビュー（5部門を横断した全社ダッシュボード）
   - `/portal/gas-station` - ミカモ石油
   - `/portal/car-coating` - カーコーティング事業（SOUP）
   - `/portal/used-car` - 中古車販売
   - `/portal/cafe` - ミカモ喫茶

2. **社内AIアシスタント**
   - ナレッジベースから関連情報を参照
   - 会話履歴管理
   - 事業部門別のコンテキスト対応

3. **ナレッジベース**
   - レシピ、オペレーションメモ、キャンペーン振り返り、マニュアル、経営方針などを蓄積
   - AIが参照可能な形式で管理

4. **日次ログ・ダッシュボード**
   - 各部門の売上・客数・取引数の記録
   - トレンドグラフ、部署間比較

**v0.2の新機能:**
- 🤖 **AI機能**: OpenAI API統合、ナレッジ連携、会話履歴対応
- 📊 **経営ダッシュボード**: 売上・客数トレンド、部署間比較グラフ
- 💬 **エンゲージメント機能**: いいね、マネージャーコメント
- 📝 **ロギング・エラーハンドリング**: JSON形式ログ、Error Boundary
- 🏢 **マルチテナント対応**: 将来の他社展開を見据えた設計

## 🎯 プロジェクトの哲学

「入力業務」をスタッフの負担にするのではなく、**「自分の仕事が認められる場」「明日のヒントが得られる場」**に変えること。

**ミカモポータルを開けば、とりあえずAIに聞けば業務の相談ができる**状態を目指しています。

## 🏢 組織構造とロール

### 事業部門（BusinessUnit）

ミカモポータルは、以下の5つの事業部門で構成されています：

1. **ミカモ石油（ガソリンスタンド）** (`gas_station`) - ガソリンスタンド事業
2. **カーコーティング事業（SOUP）** (`car_coating`) - カーコーティング事業
3. **中古車販売** (`used_car`) - 中古車販売事業
4. **ミカモ喫茶** (`cafe`) - 飲食・カフェ事業
5. **本部（HQ）** (`hq`) - 経営・経理・全社方針

### ロール（Role）

- **スタッフ** (`staff`): 自分の所属部門の情報のみ閲覧・入力可能
- **マネージャー** (`manager`): 自分の部門全体の情報を見られる部門責任者
- **経営本陣** (`head`): 5部門すべてを横断して閲覧・管理できる
- **管理者** (`admin`): システム管理者。ユーザー管理、全機能にアクセス可能

### テナント（Tenant）

現時点では単一テナント（株式会社ミカモのみ）ですが、将来的なマルチテナント化を見据えて設計されています。

- テナント: `mikamo`（株式会社ミカモ）
- 将来的に他社にも展開可能な設計

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

## 👥 みかもポータルの使い方（管理者向け）

### 組織構造とロール

みかもポータルは、以下の5つの事業部門と4つのロールで構成されています。

#### 事業部門（Department）

1. **ミカモ喫茶** (`cafe`) - 飲食・カフェ事業
2. **カーコーティング（SOUP）** (`coating`) - カーコーティング事業
3. **中古車販売** (`mnet`) - 中古車販売事業
4. **ミカモ石油（ガソリンスタンド）** (`gas`) - ガソリンスタンド事業
5. **経営本陣（本社・経営）** (`head`) - 本部・経営部門

これらの部門は、アプリ起動時に自動的に作成されます。

#### ロール（Role）

- **スタッフ** (`staff`): 一般従業員。自分が所属する部門の、自分に関係する情報のみ閲覧・入力可能
- **マネージャー** (`manager`): 部門責任者（店長・リーダー）。自分の部門全体の情報を見られる
- **経営本陣** (`head`): 経営本陣のメンバー。全ての部門を横断して集計・ダッシュボードを見られる
- **管理者** (`admin`): システム管理者。ユーザーの追加・編集・ロール変更・部門設定など全般を操作可能

### 初期管理者ユーザーの作成

本番環境では、**最初の1人の管理者ユーザー**を環境変数から自動作成します。

#### 本番環境（Cloud Run）での設定

Secret Manager に以下のシークレットを追加してください：

```bash
# 初期管理者のメールアドレス
echo -n "admin@mikamo.co.jp" | \
  gcloud secrets create MIKAMO_INITIAL_ADMIN_EMAIL \
  --project=$PROJECT_ID \
  --data-file=-

# 初期管理者のパスワード（強力なパスワードを設定してください）
echo -n "YourSecurePassword123!" | \
  gcloud secrets create MIKAMO_INITIAL_ADMIN_PASSWORD \
  --project=$PROJECT_ID \
  --data-file=-

# 初期管理者の氏名
echo -n "管理者 太郎" | \
  gcloud secrets create MIKAMO_INITIAL_ADMIN_FULL_NAME \
  --project=$PROJECT_ID \
  --data-file=-
```

Cloud Run のデプロイ時に、これらのシークレットを環境変数として注入します：

```bash
# manage_deploy.py に以下を追加（または手動で設定）
gcloud run services update mikamo-portal-backend \
  --set-secrets INITIAL_ADMIN_EMAIL=MIKAMO_INITIAL_ADMIN_EMAIL:latest \
  --set-secrets INITIAL_ADMIN_PASSWORD=MIKAMO_INITIAL_ADMIN_PASSWORD:latest \
  --set-secrets INITIAL_ADMIN_FULL_NAME=MIKAMO_INITIAL_ADMIN_FULL_NAME:latest \
  --region=$REGION \
  --project=$PROJECT_ID
```

#### ローカル開発環境での設定

`.env` ファイル（または環境変数）に以下を追加：

```bash
INITIAL_ADMIN_EMAIL=admin@mikamo.co.jp
INITIAL_ADMIN_PASSWORD=YourSecurePassword123!
INITIAL_ADMIN_FULL_NAME=管理者 太郎
```

アプリ起動時に、`role='admin'` のユーザーが存在しない場合、上記の環境変数から初期管理者ユーザーが自動作成されます。

**注意**: 既に `role='admin'` のユーザーが存在する場合、初期管理者の自動作成はスキップされます。

### 従業員ユーザーの追加方法

初期管理者ユーザーでログイン後、以下の手順で従業員を追加できます。

#### 1. 管理者画面にアクセス

- ダッシュボードのヘッダーに「ユーザー管理」ボタンが表示されます（管理者のみ）
- または、直接 `/admin/users` にアクセス

#### 2. 新規ユーザーを作成

1. 「新しいユーザーを追加」ボタンをクリック
2. 以下の情報を入力：
   - **氏名**（必須）
   - **メールアドレス**（必須）
   - **部門**（必須・セレクトボックスから選択）
   - **ロール**（必須・セレクトボックスから選択）
   - **初期パスワード**（必須・手入力または「自動生成」ボタンで生成）
3. 「作成」ボタンをクリック

#### 3. 初期パスワードの共有

作成に成功したら、**初期パスワードは別途安全な方法で共有してください**。

- メール、チャット、電話など、安全な方法で共有
- 初回ログイン時にパスワード変更を促す（v0.3以降で実装予定）

### ユーザー管理機能

管理者画面では、以下の操作が可能です：

- **ユーザー一覧の表示**: 部門・ロールで絞り込み可能
- **新規ユーザーの作成**: 上記の手順で作成
- **ユーザー情報の更新**: 氏名、部門、ロール、有効/無効フラグの変更（v0.3以降で実装予定）

### ロール別のアクセス権限

#### スタッフ（staff）
- 自分の日報の入力・閲覧
- 自分の部門の必要最低限のデータ閲覧
- AI相談機能の利用

#### マネージャー（manager）
- スタッフの全機能
- 自分の部門全体のデータ閲覧
- 部門の売上・客数トレンドグラフの閲覧
- 部下の日報へのコメント機能

#### 経営本陣（head）
- マネージャーの全機能
- 全部門を横断したデータ閲覧
- 部署間比較グラフの閲覧
- 全体のダッシュボード閲覧

#### 管理者（admin）
- 経営本陣の全機能
- ユーザー管理機能（追加・編集・削除）
- システム設定へのアクセス

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

### ミカモポータルについて

- **ミカモポータルとは**: 株式会社ミカモ専用の社内SaaS
- **5事業部門**: ミカモ石油、カーコーティング、中古車販売、ミカモ喫茶、本部
- **組織構造**: テナント／BusinessUnit／User／Role の関係
- **ポータル画面**: `/portal/hq`, `/portal/gas-station` など

### ナレッジベースについて

- **ナレッジベースとは**: ミカモグループの社内情報を蓄積・管理する機能
- **入力方法**: `/knowledge` 画面から作成・編集
- **AI連携**: AIアシスタントがナレッジベースを参照して回答

### Issue / Insight / Decision について

ミカモポータルでは、現場の質問から経営意思決定までを追跡できる仕組みを提供しています。

#### Issue（課題・困りごと）

- **定義**: 従業員がAIに質問した内容から、AIが自動的に起票する「現場の困りごと」
- **トピック**: メニュー、オペレーション、クレーム、将来リスク、売上機会、人員など
- **ステータス**: 未対応、対応中、解決済み、アーカイブ
- **閲覧**: `/issues` 画面から一覧表示（事業部門別フィルタ可能）

#### Insight（AI分析・提案）

- **定義**: 多数のIssueや会話ログから、AIが抽出した「こうした方がいいのでは？」という提案
- **タイプ**: リスク、機会、改善提案
- **重要度スコア**: 0-100（60以上の場合のみ自動生成）
- **閲覧**: `/insights` 画面から一覧表示（head/admin のみ）

#### Decision（意思決定ログ）

- **定義**: HQが下す意思決定を履歴として残し、Issue/Insightと紐づける
- **ステータス**: 計画中、進行中、完了、キャンセル
- **閲覧**: `/portal/hq` 画面から一覧表示（head/admin のみ）

### 本部ビュー（HQダッシュボード）について

`/portal/hq` では、以下の情報を一画面で確認できます：

- **健康度スコア**: 各事業部門のリスクスコア・機会スコア
- **重要なInsight**: スコアの高いAI分析・提案
- **最近のIssue**: 現場で発生している課題・困りごと
- **部署間比較**: 売上・客数・取引数の比較グラフ
- **各事業部門のサマリー**: 直近14日間の売上・客数・投稿数

これにより、「現場の声 → AIの分析 → 経営判断」が一画面で追えるようになります。

### スタッフQA用AI（現場向け軽量モデル）について

ミカモポータルでは、**現場向けの最低限AI（スタッフQA用）** と **経営判断用AI（高性能モデル）** を分離した設計になっています。

#### スタッフQA用AIの特徴

- **軽量モデル使用**: クラウドLLMの「一番軽いモデル」を使用し、コスト最適化
- **用途**: レシピ、メニューの作り方、手順書、注意事項などの現場で必要な情報を提供
- **自動判定**: スタッフ・マネージャーロールのユーザーは自動的にスタッフQAモードを使用
- **コンテキスト最適化**: 必要最小限のナレッジ情報と会話履歴のみを参照

#### 設定方法

`.env` ファイルに以下の環境変数を設定してください：

**Claude (Anthropic) API を使用する場合（推奨）:**

```bash
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF=anthropic
AI_MODEL_STAFF=claude-3-haiku-20240307  # Claude Haiku（軽量モデル）
AI_MAX_TOKENS_STAFF=1000  # 最大トークン数（コスト最適化）
AI_TEMPERATURE_STAFF=0.5  # 温度パラメータ（低めに設定）

# Anthropic (Claude) API設定
# ⚠️ 重要: ANTHROPIC_API_KEY は .env にだけ書くこと（コードやGitには絶対に入れないこと）
ANTHROPIC_API_KEY=your-claude-api-key-here
# 必要に応じてカスタムエンドポイントを指定（デフォルト: https://api.anthropic.com/v1/messages）
# ANTHROPIC_API_BASE_URL=https://api.anthropic.com/v1/messages
```

**Cloud Code API または OpenAI API を使用する場合:**

```bash
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF=cloud-code  # または "openai"
AI_MODEL_STAFF=gpt-4o-mini  # クラウド側の「一番軽いモデル」の名前
AI_MAX_TOKENS_STAFF=1000
AI_TEMPERATURE_STAFF=0.5

# Cloud Code APIを使用する場合
AI_API_KEY=your-cloud-code-api-key
AI_API_BASE_URL=https://your-cloud-code-api-endpoint.com

# OpenAI APIを使用する場合（スタッフQA用にも使える）
OPENAI_API_KEY=sk-your-openai-api-key
```

**⚠️ セキュリティ注意事項:**

- `ANTHROPIC_API_KEY` は `.env` ファイルにだけ書くこと（コードやGitには絶対に入れないこと）
- `.env` は `.gitignore` に含まれていることを確認してください
- 本番環境では Secret Manager などの安全な方法で管理してください

#### 使い方

1. **ナレッジベースに情報を登録**: `/knowledge` 画面から、レシピや手順書などの情報を登録
2. **AIに質問**: `/ai` 画面でスタッフ・マネージャーが質問すると、自動的にスタッフQAモードが使用される
3. **回答確認**: ナレッジベースから関連情報を参照した回答が返される

#### 経営判断用AI（将来実装）

将来的には、経営判断用の高性能モデルを追加する予定です。現時点では実装していませんが、設定名や関数名で用途が分かるように設計されています。

### AI機能について

v0.2から、AI機能は「DX参謀モード」にアップグレードされました。

- **5つのセクション構造**: 状況理解 → すぐできる一手 → 小さな実験 → 水平思考 → リスク
- **水平思考**: 他事業との連携アイデアを自動提案
- **小さな実験**: 1〜2週間で試せる施策を具体的に提案

詳細は `docs/V0.2_FEATURES.md` を参照してください。

## 📄 ライセンス

プロプライエタリ


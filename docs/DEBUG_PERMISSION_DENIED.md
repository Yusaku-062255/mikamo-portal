# PERMISSION_DENIED エラー デバッグガイド

`gcloud builds submit` で `PERMISSION_DENIED` エラーが発生した場合の対処方法です。

## 修正内容

`scripts/manage_deploy.py` に以下のデバッグ機能を追加しました：

1. **環境変数の明示的な引き継ぎ**: `subprocess.run` で `env=os.environ.copy()` を指定
2. **認証情報のデバッグ出力**: `gcloud builds submit` 実行前に以下を確認
   - 現在のアカウント (`gcloud config get-value account`)
   - 現在のプロジェクト (`gcloud config get-value project`)
   - Application Default Credentials の状態
3. **完全なコマンド文字列の表示**: 実行するコマンドを完全に表示

## 確認すべき事項

### 1. Cloud Build API が有効化されているか

```bash
export PROJECT_ID="soup-app-476708"

# APIの状態を確認
gcloud services list --enabled --project=$PROJECT_ID | grep cloudbuild

# 有効化されていない場合は有効化
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
```

### 2. Cloud Build の権限を確認

```bash
# 現在のアカウントでCloud Buildの権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:hiphopnewscs@gmail.com" \
  --format="table(bindings.role)"
```

必要なロール:
- `roles/cloudbuild.builds.editor` または
- `roles/owner` (既に持っているはず)

### 3. Application Default Credentials の設定

Cloud Build API を使用する場合、Application Default Credentials が必要な場合があります：

```bash
gcloud auth application-default login
```

### 4. プロジェクトの設定確認

```bash
# 現在のプロジェクトを確認
gcloud config get-value project

# プロジェクトを設定
gcloud config set project soup-app-476708
```

## デバッグ実行

修正後のスクリプトを実行すると、`Step 1` の開始時に以下のようなデバッグ情報が表示されます：

```
------------------------------------------------------------
🔍 デバッグ: gcloud認証情報の確認
------------------------------------------------------------
現在のアカウント: hiphopnewscs@gmail.com
現在のプロジェクト: soup-app-476708
✅ Application Default Credentials が設定されています
------------------------------------------------------------
```

この情報を確認して、問題を特定してください。

## よくある原因と対処法

### 原因1: Cloud Build API が有効化されていない

**対処法:**
```bash
gcloud services enable cloudbuild.googleapis.com --project=soup-app-476708
```

### 原因2: Application Default Credentials が設定されていない

**対処法:**
```bash
gcloud auth application-default login
```

### 原因3: プロジェクトIDの不一致

**対処法:**
```bash
gcloud config set project soup-app-476708
```

### 原因4: サービスアカウントの権限不足

**対処法:**
```bash
# Cloud Build サービスアカウントに権限を付与
export PROJECT_NUMBER=$(gcloud projects describe soup-app-476708 --format="value(projectNumber)")
gcloud projects add-iam-policy-binding soup-app-476708 \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

## 実行コマンド

デバッグ情報を確認しながら実行：

```bash
export PROJECT_ID="soup-app-476708"
export REGION="asia-northeast1"

python3 scripts/manage_deploy.py prod \
  --project-id "$PROJECT_ID" \
  --region "$REGION"
```

デバッグ情報を確認し、問題を特定してください。


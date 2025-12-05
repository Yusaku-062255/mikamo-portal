# AI設定ガイド（Anthropic Claude）

みかもポータルのAI機能設定に関する運用ドキュメントです。

## 概要

みかもポータルでは、Anthropic (Claude) APIを使用してAI機能を提供しています。
用途に応じて3段階のモデルティアを使い分け、コストと性能のバランスを最適化しています。

## 3段階モデルティア

### BASIC（軽量・低コスト）

| 項目 | 値 |
|------|-----|
| 用途 | シフト管理、ログ要約、簡単なタスク |
| 推奨モデル | `claude-3-haiku-20240307` |
| max_tokens | 500 |
| temperature | 0.3 |
| コスト | 最も安価 |

**対応する用途コード:**
- `shift_planning` - シフト案作成
- `log_summary` - ログの要約
- `simple_task` - 簡単な質問
- `schedule` - スケジュール関連

### STANDARD（バランス型）

| 項目 | 値 |
|------|-----|
| 用途 | 従業員Q&A、ナレッジ検索、顧客サポート |
| 推奨モデル | `claude-3-haiku-20240307` または `claude-3-5-sonnet-20241022` |
| max_tokens | 1000 |
| temperature | 0.5 |
| コスト | 中程度 |

**対応する用途コード:**
- `staff_qa` - スタッフからの質問対応
- `knowledge_search` - ナレッジベース検索
- `customer_support` - 顧客サポート
- `daily_report` - 日報分析
- `default` - デフォルト（用途未指定時）

### PREMIUM（高性能・高精度）

| 項目 | 値 |
|------|-----|
| 用途 | 経営判断支援、DXレポート分析、戦略立案 |
| 推奨モデル | `claude-3-5-sonnet-20241022` または `claude-3-opus-20240229` |
| max_tokens | 4000 |
| temperature | 0.7 |
| コスト | 最も高価 |

**対応する用途コード:**
- `management_decision` - 経営判断支援
- `dx_report` - DXレポート分析
- `strategic_planning` - 戦略立案
- `executive_summary` - 経営サマリー
- `business_analysis` - ビジネス分析

## 必要な環境変数

### 必須（本番環境）

```bash
# Anthropic API キー（Secret Manager: MIKAMO_ANTHROPIC_KEY）
ANTHROPIC_API_KEY=sk-ant-xxx...

# 3段階モデル設定
ANTHROPIC_MODEL_BASIC=claude-3-haiku-20240307
ANTHROPIC_MODEL_STANDARD=claude-3-haiku-20240307
ANTHROPIC_MODEL_PREMIUM=claude-3-5-sonnet-20241022
```

### オプション

```bash
# カスタムエンドポイント（通常は不要）
ANTHROPIC_API_BASE_URL=https://api.anthropic.com/v1/messages

# トークン数・温度のカスタマイズ
ANTHROPIC_MAX_TOKENS_BASIC=500
ANTHROPIC_MAX_TOKENS_STANDARD=1000
ANTHROPIC_MAX_TOKENS_PREMIUM=4000
ANTHROPIC_TEMPERATURE_BASIC=0.3
ANTHROPIC_TEMPERATURE_STANDARD=0.5
ANTHROPIC_TEMPERATURE_PREMIUM=0.7
```

## Secret Manager と Cloud Run の設定手順

### 1. Secret を作成する

```bash
# プロジェクトとリージョンを設定
export PROJECT_ID="soup-app-476708"
export REGION="asia-northeast1"

# Anthropic API キーの Secret を作成
# ⚠️ <YOUR_ANTHROPIC_API_KEY> を実際のキーに置き換えてください
echo -n "<YOUR_ANTHROPIC_API_KEY>" | gcloud secrets create MIKAMO_ANTHROPIC_KEY \
    --project=$PROJECT_ID \
    --data-file=-

# Secret に Cloud Run サービスアカウントへのアクセス権を付与
gcloud secrets add-iam-policy-binding MIKAMO_ANTHROPIC_KEY \
    --project=$PROJECT_ID \
    --member="serviceAccount:664388993741-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Cloud Run に Secret を紐づけて再デプロイ

**方法A: デプロイスクリプトを使用（推奨）**

```bash
cd /Users/kanemurayuusaku/mikamo_portal
python3 scripts/manage_deploy.py prod --project-id "$PROJECT_ID" --region "$REGION"
```

**方法B: 手動でサービスを更新**

```bash
# Backend サービスを更新
gcloud run services update mikamo-portal-backend \
    --project=$PROJECT_ID \
    --region=$REGION \
    --set-secrets="ANTHROPIC_API_KEY=MIKAMO_ANTHROPIC_KEY:latest" \
    --set-env-vars="ANTHROPIC_MODEL_BASIC=claude-3-haiku-20240307" \
    --set-env-vars="ANTHROPIC_MODEL_STANDARD=claude-3-haiku-20240307" \
    --set-env-vars="ANTHROPIC_MODEL_PREMIUM=claude-3-5-sonnet-20241022"
```

### 3. 設定の確認

```bash
# AI ヘルスチェックエンドポイントで確認
curl -s "https://mikamo-portal-backend-664388993741.asia-northeast1.run.app/api/ai/health" | jq
```

期待されるレスポンス:
```json
{
  "status": "healthy",
  "provider": "anthropic",
  "model": "claude-3-haiku-20240307",
  "message": "AI service is responding normally",
  "response_time_ms": 1234.56
}
```

## 将来的にモデルを差し替えるとき

### 環境変数で変更（推奨）

Cloud Run の環境変数を更新するだけで、コード変更なしにモデルを差し替えられます。

```bash
# 例: STANDARDティアをSonnetに変更
gcloud run services update mikamo-portal-backend \
    --project=$PROJECT_ID \
    --region=$REGION \
    --set-env-vars="ANTHROPIC_MODEL_STANDARD=claude-3-5-sonnet-20241022"
```

### 利用可能なモデル（2024年12月時点）

| モデル名 | 特徴 | 推奨ティア |
|---------|------|-----------|
| `claude-3-haiku-20240307` | 最速・最安価 | BASIC, STANDARD |
| `claude-3-5-sonnet-20241022` | バランス・高性能 | STANDARD, PREMIUM |
| `claude-3-opus-20240229` | 最高性能・高コスト | PREMIUM |

## コスト管理

### トークン制限

コード内で以下の制限を設けています:

- **最大トークン上限**: 8000トークン
  - 設定値がこれを超える場合、自動的にキャップされます
- **無限ループ防止**: 会話履歴は最新3件のみ参照

### コスト見積もり（参考）

| ティア | 1回あたりの目安コスト |
|--------|---------------------|
| BASIC | $0.001〜0.005 |
| STANDARD | $0.005〜0.02 |
| PREMIUM | $0.02〜0.10 |

※ 実際のコストは入力・出力トークン数により変動します

## トラブルシューティング

### エラー: "ANTHROPIC_API_KEY is not set"

**原因**: APIキーが設定されていない

**対処**:
1. Secret Manager に `MIKAMO_ANTHROPIC_KEY` が存在するか確認
2. Cloud Run サービスに Secret がマウントされているか確認
3. サービスアカウントに `secretAccessor` 権限があるか確認

### エラー: "AI model not configured for tier"

**原因**: モデル名が環境変数に設定されていない

**対処**:
```bash
gcloud run services update mikamo-portal-backend \
    --project=$PROJECT_ID \
    --region=$REGION \
    --set-env-vars="ANTHROPIC_MODEL_BASIC=claude-3-haiku-20240307" \
    --set-env-vars="ANTHROPIC_MODEL_STANDARD=claude-3-haiku-20240307" \
    --set-env-vars="ANTHROPIC_MODEL_PREMIUM=claude-3-5-sonnet-20241022"
```

### エラー: "Anthropic API authentication failed"

**原因**: APIキーが無効または期限切れ

**対処**:
1. Anthropic Console でAPIキーを確認
2. 必要に応じて新しいキーを発行
3. Secret Manager の値を更新:
   ```bash
   echo -n "<NEW_API_KEY>" | gcloud secrets versions add MIKAMO_ANTHROPIC_KEY --data-file=-
   ```

### エラー: "Anthropic API rate limit exceeded"

**原因**: APIレート制限に到達

**対処**:
- しばらく待ってから再試行
- Anthropic Console でレート制限を確認・増加リクエスト

## セキュリティチェックリスト

- [ ] APIキーが `.env.example` に含まれていないこと
- [ ] APIキーが Git にコミットされていないこと
- [ ] 本番環境では Secret Manager を使用していること
- [ ] サービスアカウントに最小限の権限のみ付与していること
- [ ] max_tokens の上限が適切に設定されていること

## ログの確認方法

### Cloud Run ログでAI呼び出しを確認

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mikamo-portal-backend AND jsonPayload.message:\"Anthropic API\"" \
    --project=$PROJECT_ID \
    --limit=20 \
    --format="table(timestamp,jsonPayload.message,jsonPayload.model,jsonPayload.tier)"
```

### ティア別の利用状況を確認

ログに以下の情報が出力されます:
- `purpose`: 用途名
- `tier`: 使用されたティア (basic/standard/premium)
- `model`: 使用されたモデル名
- `usage`: トークン使用量

---

更新日: 2024年12月4日

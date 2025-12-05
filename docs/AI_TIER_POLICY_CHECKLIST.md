# AIティアポリシー 手動確認チェックリスト

本ドキュメントでは、AIティアポリシー（`ai_tier_policy`）の動作を手動で確認する手順を説明します。

## 前提条件

- 管理者（admin）アカウントでログインできること
- スタッフ（staff）アカウントが存在すること（動作確認用）
- Cloud Loggingまたはローカルログにアクセスできること

---

## 1. AIプランの変更（管理者操作）

### 手順

1. **管理者でログイン**
   - フロントエンド: `https://mikamo-portal-frontend-xxx.run.app/login`
   - adminロールのアカウントでログイン

2. **テナント設定画面へ移動**
   - ユーザー管理画面 → 「テナント設定」ボタン
   - または直接 `/admin/settings` へアクセス

3. **AIモデルプランを変更**
   - 「AI設定」セクション → 「AIモデルプラン」を選択
     - **プレミアムプラン（全ティア利用可能）**: `all`
     - **スタンダードプラン（STANDARD以下）**: `standard_max`
     - **ライトプラン（BASICのみ）**: `basic_only`
   - 「設定を保存」をクリック

4. **保存成功を確認**
   - 「設定を保存しました」メッセージが表示されること

---

## 2. スタッフユーザーでのAI動作確認

### 手順

1. **スタッフアカウントでログイン**
   - 別ブラウザまたはシークレットウィンドウでログイン
   - staffロールのアカウントを使用

2. **AIに質問画面へ移動**
   - サイドバー → 「AIに質問」
   - または直接 `/ai` へアクセス

3. **質問を送信**
   - 簡単な質問を入力して送信
   - 例: 「今日のおすすめメニューは？」

4. **応答を確認**
   - AIからの応答が返ってくることを確認

---

## 3. ログでのティア確認

### Cloud Logging（本番環境）

1. **Google Cloud Console**へアクセス
   - https://console.cloud.google.com/logs

2. **ログクエリを実行**
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="mikamo-portal-backend"
   jsonPayload.message:"Creating AI client"
   ```

3. **確認ポイント**
   - `purpose`: 用途（"staff_qa", "management_decision" など）
   - `tier` または `original_tier`: 用途から決定されたティア
   - `effective_tier`: ポリシー適用後の実際のティア
   - `model`: 使用されたモデル名

### ローカル開発環境

1. **バックエンドのコンソール出力を確認**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **ログ出力例**
   ```
   Creating AI client with tier policy
     purpose=staff_qa
     original_tier=standard
     effective_tier=basic  # BASIC_ONLYポリシーの場合
     model=claude-3-haiku-20240307
   ```

---

## 4. 期待される動作一覧

| AIプラン | 用途 | 元のティア | 適用後ティア | 使用モデル（例） |
|---------|------|-----------|-------------|----------------|
| プレミアム（all） | staff_qa | STANDARD | STANDARD | claude-3-sonnet |
| プレミアム（all） | management_decision | PREMIUM | PREMIUM | claude-3-opus |
| スタンダード（standard_max） | staff_qa | STANDARD | STANDARD | claude-3-sonnet |
| スタンダード（standard_max） | management_decision | PREMIUM | **STANDARD** | claude-3-sonnet |
| ライト（basic_only） | staff_qa | STANDARD | **BASIC** | claude-3-haiku |
| ライト（basic_only） | management_decision | PREMIUM | **BASIC** | claude-3-haiku |

---

## 5. トラブルシューティング

### ティアが変わらない場合

1. **キャッシュをクリア**
   - ブラウザのキャッシュをクリアして再ログイン

2. **設定が保存されているか確認**
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" \
     https://mikamo-portal-backend-xxx.run.app/api/tenant/settings
   ```
   - `ai_tier_policy` の値を確認

3. **バックエンドの再デプロイ**
   - Cloud Runの場合、新しいリビジョンをデプロイ

### ログが出力されない場合

1. **ログレベルを確認**
   - `structlog` の設定でINFOレベル以上が出力されているか

2. **Cloud Loggingのフィルタを調整**
   - 時間範囲を広げる
   - severity を ALL に変更

---

## 6. 自動テスト

ユニットテストでロジックを確認できます：

```bash
cd backend
pip install pytest
pytest tests/test_ai_tier_policy.py -v
```

テスト内容：
- `apply_tier_policy()`: ポリシー適用ロジック
- `get_tier_for_purpose()`: 用途→ティアマッピング
- 統合テスト: 用途+ポリシーの組み合わせ

---

## 更新履歴

- 2024-12-05: 初版作成

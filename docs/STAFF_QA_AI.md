# スタッフQA用AI（現場向け軽量モデル）の実装

## 概要

ミカモポータルでは、**現場向けの最低限AI（スタッフQA用）** と **経営判断用AI（高性能モデル）** を分離した設計になっています。

今回実装したのは「スタッフQA用AI」で、Claude Haiku（Anthropic）などの「軽量モデル」を使用し、コスト最適化を意識した設計です。

## 最新の更新 (2025年12月)

- **AIヘルスチェックエンドポイント追加**: `/api/ai/health` でAI設定の確認が可能
- **ナレッジモデル拡張**: `category`, `source` フィールドを追加
- **DXレポートシードスクリプト**: 6セクションのDXレポートを自動登録

## コンセプト

### スタッフQA用AIの役割

- **用途**: レシピ、メニューの作り方、手順書、注意事項などの現場で必要な情報を提供
- **対象ユーザー**: スタッフ・マネージャー
- **モデル**: クラウドLLMの「一番軽いモデル」（コスト最適化）
- **コンテキスト**: 必要最小限のナレッジ情報と会話履歴のみ

### 経営判断用AI（将来実装）

- **用途**: 経営判断レベルの複雑な分析
- **対象ユーザー**: 経営本陣（head）、管理者（admin）
- **モデル**: 高性能モデル（将来実装）
- **現状**: プレースホルダのみ、実装は未実装

## 技術実装

### 1. 設定項目

`backend/app/core/config.py` に以下の設定を追加：

```python
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF: str = "cloud-code"  # スタッフQA用プロバイダー
AI_MODEL_STAFF: str = "gpt-4o-mini"  # クラウド側の「一番軽いモデル」
AI_MAX_TOKENS_STAFF: int = 1000  # 最大トークン数（コスト最適化）
AI_TEMPERATURE_STAFF: float = 0.5  # 温度パラメータ（低めに設定）
```

### 2. AiClientFactory の拡張

`backend/app/services/ai/client.py` に `get_staff_client()` メソッドを追加：

- スタッフQA用の軽量モデルClientを取得
- `AI_PROVIDER_STAFF` / `AI_MODEL_STAFF` を参照

### 3. StaffQAService の実装

`backend/app/services/staff_qa_service.py` を新規作成：

- スタッフQA用の回答生成ロジック
- 必要最小限のコンテキスト構築
- ナレッジベースからの関連情報検索（最大3件）
- 直近の会話履歴（最新3件まで）

### 4. /api/ai/chat の拡張

`backend/app/api/ai_chat.py` にスタッフQAモードを組み込み：

- リクエストに `mode: "staff_qa"` パラメータを追加
- スタッフ・マネージャーの場合は自動的にスタッフQAモードを使用
- それ以外は既存の通常モード（経営判断用）を使用

### 5. AIヘルスチェックエンドポイント

`GET /api/ai/health` でAI設定の確認が可能：

```json
{
  "status": "ok",
  "provider": "anthropic",
  "model": "claude-3-haiku-20240307",
  "api_key_configured": true,
  "max_tokens": 1000,
  "temperature": 0.5
}
```

### 6. ナレッジモデルの拡張

`backend/app/models/knowledge_item.py` に新しいフィールドを追加：

- `category`: カテゴリ（例：DXレポート、レシピ、マニュアル）
- `source`: 情報元（例：Claude AI調査レポート）

### 7. DXレポートシードスクリプト

`backend/scripts/seed_dx_knowledge.py` でDXレポートを自動登録：

```bash
cd backend
python scripts/seed_dx_knowledge.py
```

6つのセクションに分割されたDXレポートをナレッジベースに登録します。

### 8. フロントエンド調整

`frontend/src/pages/AIChat.tsx` を更新：

- API呼び出し時に `mode: "staff_qa"` を付与（スタッフ・マネージャーの場合）

## 環境変数設定

`.env` ファイルに以下の環境変数を設定：

### Claude (Anthropic) API を使用する場合（推奨）

```bash
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF=anthropic
AI_MODEL_STAFF=claude-3-haiku-20240307  # Claude Haiku（軽量モデル）
AI_MAX_TOKENS_STAFF=1000
AI_TEMPERATURE_STAFF=0.5

# Anthropic (Claude) API設定
# ⚠️ 重要: ANTHROPIC_API_KEY は .env にだけ書くこと（コードやGitには絶対に入れないこと）
ANTHROPIC_API_KEY=your-claude-api-key-here
# 必要に応じてカスタムエンドポイントを指定（デフォルト: https://api.anthropic.com/v1/messages）
# ANTHROPIC_API_BASE_URL=https://api.anthropic.com/v1/messages
```

### Cloud Code API を使用する場合

```bash
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF=cloud-code
AI_MODEL_STAFF=gpt-4o-mini  # クラウド側の「一番軽いモデル」の名前
AI_MAX_TOKENS_STAFF=1000
AI_TEMPERATURE_STAFF=0.5

# Cloud Code APIを使用する場合
AI_API_KEY=your-cloud-code-api-key
AI_API_BASE_URL=https://your-cloud-code-api-endpoint.com
```

### OpenAI API を使用する場合

```bash
# スタッフQA用軽量モデル設定
AI_PROVIDER_STAFF=openai
AI_MODEL_STAFF=gpt-4o-mini
AI_MAX_TOKENS_STAFF=1000
AI_TEMPERATURE_STAFF=0.5

# OpenAI APIを使用する場合
OPENAI_API_KEY=sk-your-openai-api-key
```

## 使い方

1. **ナレッジベースに情報を登録**
   - `/knowledge` 画面から、レシピや手順書などの情報を登録
   - 事業部門（例: ミカモ喫茶）を指定して登録

2. **AIに質問**
   - `/ai` 画面でスタッフ・マネージャーが質問
   - 自動的にスタッフQAモードが使用される

3. **回答確認**
   - ナレッジベースから関連情報を参照した回答が返される
   - 会話履歴も参照されるため、継続的な対話が可能

## コスト最適化のポイント

1. **軽量モデル使用**: クラウド側の「一番軽いモデル」を指定
2. **トークン数制限**: `AI_MAX_TOKENS_STAFF=1000` で応答長を制限
3. **コンテキスト最小化**: ナレッジ情報は最大3件、会話履歴は最新3件まで
4. **温度パラメータ**: `AI_TEMPERATURE_STAFF=0.5` で低めに設定（一貫性重視）

## 将来の拡張

### 経営判断用AI（将来実装）

- `AI_PROVIDER_EXECUTIVE`: 経営判断用プロバイダー
- `AI_MODEL_EXECUTIVE`: 経営判断用高性能モデル
- `AiClientFactory.get_executive_client()`: 経営判断用Client取得（プレースホルダ）

### トークン使用量の記録

将来的には、`Message` テーブルに以下のメタデータを保存できるようにする：

- `prompt_tokens`: プロンプトのトークン数
- `completion_tokens`: 応答のトークン数
- `model_name`: 使用したモデル名

これにより、コスト計算や使用量の可視化が可能になります。

## トラブルシューティング

### スタッフQAモードが使われない

- ユーザーのロールが `staff` または `manager` であることを確認
- または、APIリクエストに `mode: "staff_qa"` を明示的に指定

### ナレッジベースの情報が参照されない

- `/knowledge` 画面で、該当する事業部門に紐づくナレッジが登録されているか確認
- ナレッジのタイトル・本文に、質問に関連するキーワードが含まれているか確認

### APIエラーが発生する

- `.env` ファイルに `AI_PROVIDER_STAFF` と `AI_MODEL_STAFF` が正しく設定されているか確認
- **Claude (Anthropic) APIを使用する場合**:
  - `ANTHROPIC_API_KEY` が正しく設定されているか確認
  - APIキーが有効か確認（Anthropicのダッシュボードで確認）
  - `ANTHROPIC_API_BASE_URL` が正しく設定されているか確認（デフォルトは公式エンドポイント）
- Cloud Code APIを使用する場合、`AI_API_BASE_URL` が正しく設定されているか確認
- OpenAI APIを使用する場合、`OPENAI_API_KEY` が正しく設定されているか確認

### Claude APIキーのセキュリティ

⚠️ **重要**: `ANTHROPIC_API_KEY` は以下の点に注意してください：

- `.env` ファイルにだけ書くこと（コードやGitには絶対に入れないこと）
- `.env` は `.gitignore` に含まれていることを確認
- 本番環境では Secret Manager などの安全な方法で管理すること
- APIキーが漏洩した場合は、すぐにAnthropicのダッシュボードで無効化すること


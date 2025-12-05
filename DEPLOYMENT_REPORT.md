# みかもポータル デプロイメントレポート

**作成日:** 2025年12月4日
**プロジェクト:** soup-app-476708
**リージョン:** asia-northeast1

---

## 1. タスク完了状況

| タスク | ステータス | 備考 |
|--------|------------|------|
| Vite allowedHosts問題の修正 | 完了 | `vite.config.ts`に`allowedHosts: true`を追加 |
| フロントエンドCloud Runデプロイ | 完了 | リビジョン: mikamo-portal-frontend-00009-v84 |
| Cloud SQL統合確認 | 完了 | PostgreSQL 16で正常稼働 |

---

## 2. Cloud Run サービス URL

### 本番環境

| サービス | URL |
|----------|-----|
| **フロントエンド** | https://mikamo-portal-frontend-664388993741.asia-northeast1.run.app |
| **バックエンド** | https://mikamo-portal-backend-664388993741.asia-northeast1.run.app |

### 代替URL（同一サービス）

| サービス | URL |
|----------|-----|
| フロントエンド | https://mikamo-portal-frontend-27z4hvqqla-an.a.run.app |
| バックエンド | https://mikamo-portal-backend-27z4hvqqla-an.a.run.app |

---

## 3. Cloud SQL 統合状況

### インスタンス情報

| 項目 | 値 |
|------|-----|
| インスタンス名 | `mikamoportal` |
| データベースバージョン | PostgreSQL 16 |
| リージョン | asia-northeast1 |
| マシンタイプ | db-custom-2-8192 |
| ステータス | RUNNABLE（稼働中） |

### 接続設定

- **Cloud SQL接続**: `soup-app-476708:asia-northeast1:mikamoportal`
- **DATABASE_URL**: Secret Manager (`MIKAMO_DB_URL`) から取得
- **接続方式**: Cloud Run ⇔ Cloud SQL Auth Proxy（自動）

### 環境変数（Secret Manager管理）

| 環境変数 | シークレット名 |
|----------|----------------|
| DATABASE_URL | MIKAMO_DB_URL |
| JWT_SECRET_KEY | MIKAMO_JWT_SECRET |
| OPENAI_API_KEY | MIKAMO_OPENAI_KEY |

---

## 4. 実施した修正

### 4.1 Vite allowedHosts問題の修正

**問題:** iPhoneなどのモバイルデバイスからCloud Run上のフロントエンドにアクセスすると「Blocked request. This host is not allowed.」エラーが発生

**原因:** Viteの開発サーバーがホスト名を検証し、Cloud Runの動的ホスト名をブロック

**修正内容:**

```typescript
// frontend/vite.config.ts
server: {
  host: true,
  port: 5173,
  allowedHosts: true,  // 追加：全ホスト名を許可
  watch: {
    usePolling: true
  }
},
preview: {
  host: true,
  allowedHosts: true   // 追加：プレビューモード用
}
```

### 4.2 事業部門（BusinessUnit）機能

以前のセッションで実装済み：

- 5つの事業部門を作成
  - ミカモ石油 (gas)
  - カーコーティング SOUP (coating)
  - 中古車販売 Mnet (mnet)
  - みかも喫茶 (cafe)
  - 本部 (hq)

- ロールベースアクセス制御
  - admin/head: 全社閲覧可
  - staff/manager: 自部門 + 共通のみ

---

## 5. アーキテクチャ概要

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ブラウザ      │────▶│   Cloud Run     │────▶│   Cloud Run     │
│   (iPhone等)    │     │   Frontend      │     │   Backend       │
└─────────────────┘     │   (Vite/React)  │     │   (FastAPI)     │
                        └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Secret Manager │     │   Cloud SQL     │
                        │  (認証情報管理)  │     │   PostgreSQL 16 │
                        └─────────────────┘     └─────────────────┘
```

---

## 6. 今後の推奨事項

### 6.1 セキュリティ

- [ ] CORS設定の更新（現在は旧URLが設定されている可能性）
- [ ] HTTPS強制の確認
- [ ] レート制限の実装検討

### 6.2 パフォーマンス

- [ ] フロントエンドのコード分割（現在782KBのバンドルサイズ）
- [ ] CDN導入の検討（静的アセット配信）

### 6.3 運用

- [ ] Cloud Loggingでのモニタリング設定
- [ ] アラート設定（エラー率、レイテンシ）
- [ ] 定期バックアップの確認

### 6.4 開発ワークフロー

- [ ] CI/CDパイプラインの構築（GitHub Actions等）
- [ ] ステージング環境の整備

---

## 7. 動作確認結果

| テスト項目 | 結果 |
|------------|------|
| フロントエンドアクセス | HTTP 200 OK |
| バックエンドAPI | 正常応答（認証エンドポイント動作確認） |
| Cloud SQL接続 | RUNNABLE（稼働中） |

---

## 8. 参考コマンド

### デプロイ

```bash
# フロントエンドビルド＆デプロイ
cd frontend
npm run build
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/soup-app-476708/mikamo-portal/frontend:latest .
gcloud run deploy mikamo-portal-frontend \
  --image asia-northeast1-docker.pkg.dev/soup-app-476708/mikamo-portal/frontend:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 5173

# バックエンドビルド＆デプロイ
cd backend
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/soup-app-476708/mikamo-portal/backend:latest .
gcloud run deploy mikamo-portal-backend \
  --image asia-northeast1-docker.pkg.dev/soup-app-476708/mikamo-portal/backend:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated
```

### 状態確認

```bash
# Cloud Runサービス一覧
gcloud run services list --region asia-northeast1 --project soup-app-476708

# Cloud SQLインスタンス確認
gcloud sql instances describe mikamoportal --project soup-app-476708

# ログ確認
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --project soup-app-476708
```

---

**以上**

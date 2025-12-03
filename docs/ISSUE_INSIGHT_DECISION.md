# Issue / Insight / Decision の概念と使い方

## 概要

ミカモポータルでは、**現場Q&Aから経営意思決定までつながる**仕組みを提供しています。

## 1. Issue（課題・困りごと）

### 定義

従業員がAIに質問した内容から、AIが自動的に起票する「現場の困りごと・トピック」です。

### 特徴

- **自動生成**: AIが重要な質問を判断し、自動的にIssueを作成
- **トピック分類**: メニュー、オペレーション、クレーム、将来リスク、売上機会、人員など
- **ステータス管理**: 未対応 → 対応中 → 解決済み → アーカイブ

### トピック一覧

- `menu`: メニュー・レシピ
- `operation`: オペレーション・手順
- `customer_complaint`: クレーム
- `future_risk`: 将来リスク（例：EV化によるガソリンスタンド事業のリスク）
- `sales_opportunity`: 売上機会
- `staffing`: 人員・採用
- `other`: その他

### 使い方

1. **AIに質問**: `/ai` 画面でAIに質問する
2. **自動生成**: AIが重要な質問を判断し、自動的にIssueを作成
3. **確認**: `/issues` 画面で課題一覧を確認
4. **対応**: マネージャーやHQがIssueを確認し、対応状況を更新

## 2. Insight（AI分析・提案）

### 定義

多数のIssueや会話ログから、AIが抽出した「こうした方がいいのでは？」という提案・分析です。

### 特徴

- **自動生成**: AIが複数のIssueから重要な気付きを抽出
- **重要度スコア**: 0-100（60以上の場合のみ自動生成）
- **タイプ分類**: リスク、機会、改善提案

### タイプ一覧

- `risk`: リスク（例：「EV普及に伴うガソリンスタンド依存リスク」）
- `opportunity`: 機会（例：「中古車部門へのリソース強化の提案」）
- `improvement`: 改善提案（例：「喫茶の客単価向上施策」）

### 使い方

1. **自動生成**: AIが複数のIssueからInsightを自動生成
2. **確認**: `/insights` 画面で重要なInsightを確認（head/admin のみ）
3. **意思決定**: HQがInsightを元にDecisionを作成

## 3. Decision（意思決定ログ）

### 定義

HQが下す意思決定を履歴として残し、Issue/Insightと紐づけるものです。

### 特徴

- **意思決定の可視化**: 「どんな判断をしたか」「何をいつまでにやるか」を記録
- **ステータス管理**: 計画中 → 進行中 → 完了 → キャンセル
- **関連付け**: 関連するInsightと紐づけることで、意思決定の根拠を明確化

### 使い方

1. **Insightを確認**: `/portal/hq` で重要なInsightを確認
2. **Decisionを作成**: HQがInsightを元にDecisionを作成
3. **進捗管理**: ステータスを更新しながら進捗を管理

## 4. フロー例

### 例1: ミカモ喫茶のメニューに関する質問

1. **現場**: 「ミカモ喫茶のコーヒーの淹れ方がわからない」とAIに質問
2. **AI**: ナレッジベースからレシピを参照して回答
3. **Issue生成**: AIが「メニュー・レシピ」トピックのIssueを自動生成
4. **Insight生成**: 複数のメニュー関連Issueから「レシピマニュアルの整備が必要」というInsightを生成
5. **Decision**: HQが「レシピマニュアルを作成する」というDecisionを作成

### 例2: EV化による将来リスク

1. **現場**: 「EV化でガソリンスタンドの将来が不安」とAIに質問
2. **AI**: 将来リスクについて分析・提案
3. **Issue生成**: AIが「将来リスク」トピックのIssueを自動生成
4. **Insight生成**: 複数の将来リスク関連Issueから「EVシフトに備えた事業転換が必要」というInsightを生成
5. **Decision**: HQが「◯年以内に石油部門の売上依存度を◯％以下にする」というDecisionを作成

## 5. 本部ビュー（HQダッシュボード）

`/portal/hq` では、以下の情報を一画面で確認できます：

- **健康度スコア**: 各事業部門のリスクスコア・機会スコア
- **重要なInsight**: スコアの高いAI分析・提案
- **最近のIssue**: 現場で発生している課題・困りごと
- **部署間比較**: 売上・客数・取引数の比較グラフ

これにより、「現場の声 → AIの分析 → 経営判断」が一画面で追えるようになります。

## 6. スコアリング

### BusinessUnitHealth（事業部門の健康度）

各事業部門のリスクスコア・機会スコアを自動計算します。

#### リスクスコアの計算ロジック

- 将来リスク系Issueが少ない = 危機感が薄い = リスクを上げる（+20）
- クレーム系Issueが多い = リスクを上げる（+5 × 件数、最大+30）
- リスクタイプのInsightが多い = リスクを上げる（+スコア合計 ÷ 10、最大+30）

#### 機会スコアの計算ロジック

- 機会タイプのInsightが多い = 機会スコアを上げる（+スコア合計 ÷ 10、最大+40）
- 売上機会系Issueが多い = 機会スコアを上げる（+10 × 件数、最大+30）
- 日報の投稿頻度が高い = 現場のエンゲージメントが高い = 機会スコアを上げる（+投稿数 ÷ 2、最大+20）

## 7. 開発者向けメモ

### データモデル

- `Issue`: `backend/app/models/issue.py`
- `Insight`: `backend/app/models/insight.py`
- `Decision`: `backend/app/models/decision.py`
- `BusinessUnitHealth`: `backend/app/models/business_unit_health.py`

### APIエンドポイント

- `/api/issues/*`: IssueのCRUD
- `/api/insights/*`: InsightのCRUD
- `/api/decisions/*`: DecisionのCRUD
- `/api/portal/hq/health`: 健康度スコア取得

### 自動生成ロジック

- `backend/app/services/issue_insight_extractor.py`: AIレスポンスからIssue/Insightを抽出
- `backend/app/services/business_unit_health_service.py`: 健康度スコアの計算

### フロントエンド画面

- `/issues`: Issue一覧
- `/insights`: Insight一覧（head/admin のみ）
- `/portal/hq`: 本部ビュー（健康度スコア、Insight、Issueを一覧表示）


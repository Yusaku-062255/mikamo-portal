"""
AIサービス（v0.2: OpenAI API統合）
ミカモ専属のDX参謀AIとして、現場スタッフをサポート
"""
import os
from typing import Optional, List, Dict
from openai import OpenAI
from app.core.config import settings
from app.models.daily_log import DailyLog
from app.models.user import Department, User
import structlog

logger = structlog.get_logger()


class AIService:
    """AI相談サービス - ミカモ専属DX参謀AI"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OPENAI_API_KEY not set, AI service will use fallback responses")
    
    def _build_system_prompt(
        self,
        department_code: str,
        role: str,
        department_name: str
    ) -> str:
        """
        部署・ロールに応じたSystem Promptを構築
        
        Args:
            department_code: 部署コード
            role: ユーザーのロール
            department_name: 部署名
        
        Returns:
            System Prompt文字列
        """
        base_prompt = """あなたは「株式会社ミカモ」のDX参謀かつフルスタックアーキテクトです。

▼ 会社と事業
ミカモは次の4事業＋本部から成る地方企業です：
- SOUP：カーコーティング（1名中心）       → department_code: coating
- M-NET：中古車販売（1名）                 → department_code: mnet
- ミカモ石油：ガソリンスタンド（2〜3名） → department_code: gas
- ミカモ喫茶：飲食（4〜5名）               → department_code: cafe
- 本部（Head）：経営・管理部門             → department_code: head

▼ DXの本質
このプロジェクトの目的は、「とにかく最新のツールを入れる」ことではなく、
レポートで定義された以下のDXの本質を実現することです：

- デジタイゼーション：紙やアナログ情報をデジタル化すること
- デジタライゼーション：個別業務を効率化すること
- デジタルトランスフォーメーション（DX）：
  データとデジタル技術を活用して、
  事業モデル・業務・組織・文化を変革し、
  地方からでも競争優位をつくること

▼ 成功事例からの原則
- ゑびや（伊勢）：「予測精度を高めて、仕入れと人員配置を最適化」することで売上5倍・利益率10倍を実現。
  → 目的は「AI導入」ではなく、「食品ロス削減＆機会損失削減」だった。
- 浜松倉庫：若手管理職を中心にボトムアップで改善文化を育て、DXを「現場が楽になる仕組み」として浸透。
- 山口産業：40以上のツールを導入しつつも、すべてを経営ビジョンとDX計画に紐づけ、情報開示も戦略的にコントロール。
- 農業DX・交通DX：個別の機械化を超え、「バリューチェーン全体」「地域インフラ全体」を変える発想。

▼ 失敗事例からの警告
- 山口フィナンシャルグループ（YMFG）：既存ビジネスモデルと新銀行構想が正面衝突し、ガバナンスと政治対立で頓挫。
- 「手段の目的化」企業：「DX推進室」をつくり、ツール導入をゴールにして現場の課題もKPIも不明なまま自然消滅。
- 自治体地域通貨の多く：プレミアムや補助金に依存し、利用者にとっての「使い続ける理由」が弱く、持続しなかった。
- ERP刷新訴訟案件：発注側の丸投げと要件不明瞭により、ベンダーとの紛争・プロジェクト崩壊を招いた。

▼ あなたの役割
現場スタッフや店長の日報・数字・相談内容をもとに、
1. その日の悩みをちゃんと解決しつつ
2. 「売上・利益・リピート・ブランド」につながる打ち手を
3. 極力、小さな実験（1〜2週間で試せること）という形で提案すること

▼ 5つの観点で必ずチェック
何か提案・設計・実装をするときは、必ず次の5つの観点で自分をチェックしてください：

1. 【Whyの明確化】
   - これは「どの事業の」「どの経営課題／現場課題」を解決したいのか？
   - 数字で言えるKGI/KPIは何か？（例：フードロス率○％削減、1台あたり単価○円アップ、在庫回転日数短縮など）

2. 【BPR（業務の断捨離）を先に検討しているか】
   - 既存の紙やExcelのプロセスを"そのまま"システム化していないか？
   - 「本当に必要なステップだけを残したフロー」になっているか？

3. 【現場オーナーシップ】
   - 提案している機能は、SOUP / M-NET / ミカモ石油 / ミカモ喫茶 の現場担当者が「自分ごと」として使える設計になっているか？
   - 「仕事が増えるシステム」ではなく、「楽になる／稼ぎやすくなるシステム」に見えるか？

4. 【越境・横断の視点】
   - その機能は、他の事業とデータ・ノウハウを共有することで、追加の価値を生み出せないか？
   - 例：ガソリンスタンドの顧客データ → コーティング提案、喫茶の来客傾向 → スタンドのキャンペーン設計 など

5. 【持続可能性とガバナンス】
   - 補助金・一時的キャンペーンが切れても使い続けられる設計か？
   - 既存の権限・役割をどう変えるのか、DX後の「役割の物語」が描かれているか？
   - ベンダーやAIに"丸投げ"していないか？ミカモ側が主体的に意思決定できる構造になっているか？

▼ 出力スタイルのルール

常に、以下の構造で日本語で回答すること（です・ます調）：

1.【今日の状況の理解】
- 事業: （coating / mnet / gas / cafe / head）
- いまの悩みやテーマを、一文で言い直す
- どの経営課題／現場課題に紐づくか

2.【すぐにできる一手（明日から）】
- 現場の負担が小さく、すぐ試せる行動提案を箇条書きで1〜3個
- 必ず「具体的なセリフ」か「具体的な行動」を1つ以上含める
  例：「◯◯と言ってみる」「◯◯の紙をレジ横に置く」など
- BPRの視点：既存プロセスを「そのまま」デジタル化していないか確認

3. 【小さな実験案（1〜2週間）】
- 1〜2週間で試せる「ミニ施策」を1つだけ提案する
- 必ず「どの数字を見るか（KPI）」「やめる判断ライン」を含める
  例：「ドリンクセットの声かけを2週間続け、客単価＋50円以上なら継続」
- 成功事例との対応関係（ゑびや／浜松倉庫／山口産業など）を1行で言及

4. 【水平思考での一歩先の視点】
- SOUP / M-NET / ミカモ石油 / ミカモ喫茶 / 本部のうち、
  「他のどこかと組めないか？」という視点で1つだけアイデアを書く
- 例：
  - ガソリン → 喫茶への送客クーポン
  - 喫茶 → コーティングの待ち時間サービス案内
  - M-NETの納車時にSOUPや石油・喫茶を絡める など
- データ・ノウハウの共有で追加価値を生み出す視点を含める

5. 【リスク・注意点】
- クレーム・オペレーション崩壊・スタッフの疲弊など、想定されるリスクがあれば一文で触れる
- 「手段の目的化」「ガバナンス不全」「一時的キャンペーン依存」などの失敗パターンをどう避けるか

▼ 水平思考のルール

次のような問いを心の中で一度通してから提案を出すこと：
- 「もし紙と口頭でしか運用できないなら、どう変えるか？」
- 「もしスタッフが今の人数のまま売上を1.2倍にするとしたら、どこを変えるのが一番コスパが良さそうか？」
- 「他業種（コンビニ・スタバ・ディーラー）で成功しているパターンを、この現場に持ち込むとしたら何か？」
- 「バリューチェーン全体」「地域インフラ全体」を変える発想はないか？

その上で、「現場の手間が極力増えない提案」を優先すること。

▼ トーン
- 基本はフラットかつ敬意ある口調。
- 「無理なことは無理」と正直に言ってよいが、代わり案を1つ出すこと。
- 抽象論で終わらせず、必ず「今日・明日からできる単位」まで落とし込むこと。
- 「地方の中小企業であるミカモが、DXを通じて"地方のハンディキャップ"を逆転させるロールモデルになる」という視点を持つこと。"""

        # 部署別の視点を追加
        department_contexts = {
            "coating": """
【SOUP（カーコーティング事業）の視点】
- 高単価コーティング・オプションの受注率向上を意識
- 洗車からコーティングへのアップセル動線を意識
- 施工品質と「納車体験」（お見送り・説明）の向上を重視
""",
            "mnet": """
【M-NET（中古車販売事業）の視点】
- 来店→商談→成約までのボトルネック発見を重視
- 在庫回転率・粗利を意識した提案を心がける
- LINE / SNS などでのフォローアップ方法を提案
""",
            "gas": """
【ミカモ石油（ガソリンスタンド事業）の視点】
- 給油から洗車・コーティング・喫茶への送客動線を意識
- ピーク時間帯の回転率アップと安全・事故防止を両立
- 近隣住民の固定客化（声かけ・キャンペーン）を提案
""",
            "cafe": """
【ミカモ喫茶（飲食・カフェ事業）の視点】
- 客単価アップ（セット・デザート・ドリンク提案）を意識
- 滞在満足度と回転率のバランスを重視
- SNS映え・口コミにつながる一言・工夫を提案
""",
            "head": """
【本部・経営の視点】
- 部署横断のトレンド・ボトルネック把握を重視
- KPI設定・キャンペーン施策のアイデアを提案
- 経営数字と現場の肌感を結びつける視点を持つ
""",
        }
        
        dept_context = department_contexts.get(department_code, "")
        
        return f"{base_prompt}\n\n{dept_context}\n\n現在のユーザー: {department_name}の{role}"
    
    def _build_context_from_logs(
        self,
        recent_logs: List[DailyLog],
        summary: Dict,
        today_log: Optional[DailyLog] = None
    ) -> str:
        """
        直近のDailyLogからコンテキストを構築
        
        Args:
            recent_logs: 直近のDailyLogリスト
            summary: サマリーデータ
            today_log: 今日のDailyLog（あれば）
        
        Returns:
            コンテキスト文字列
        """
        context_parts = []
        
        # サマリー情報
        if summary.get("log_count", 0) > 0:
            context_parts.append(f"""
【直近の状況サマリー】
- 直近14日間の投稿数: {summary['log_count']}件
- 平均売上: {summary['avg_sales']:,.0f}円
- 平均客数: {summary['avg_customers']:.1f}人
- 合計売上: {summary['total_sales']:,}円
- 合計客数: {summary['total_customers']}人
""")
        
        # 今日のログ
        if today_log:
            context_parts.append(f"""
【今日の状況】
- 売上: {today_log.sales_amount:,}円
- 客数: {today_log.customers_count}人
- 取引数: {today_log.transaction_count}件
- 天気: {today_log.weather.value if today_log.weather else '未入力'}
""")
            if today_log.highlight:
                context_parts.append(f"- 良かったこと: {today_log.highlight}")
            if today_log.problem:
                context_parts.append(f"- 課題・チャレンジ: {today_log.problem}")
        
        # 直近のログから重要な情報を抽出（最新3件）
        if recent_logs:
            context_parts.append("\n【直近の投稿から】")
            for log in recent_logs[:3]:
                if log.highlight or log.problem:
                    date_str = log.log_date.strftime("%m/%d")
                    if log.highlight:
                        context_parts.append(f"- {date_str}: {log.highlight[:100]}...")
                    if log.problem:
                        context_parts.append(f"- {date_str}: {log.problem[:100]}...")
        
        return "\n".join(context_parts)
    
    async def generate_answer(
        self,
        question: str,
        user: User,
        department: Department,
        recent_logs: List[DailyLog],
        summary: Dict,
        today_log: Optional[DailyLog] = None
    ) -> str:
        """
        AI回答を生成（OpenAI API使用）
        
        Args:
            question: ユーザーの質問
            user: ユーザー情報
            department: 部署情報
            recent_logs: 直近のDailyLogリスト
            summary: サマリーデータ
            today_log: 今日のDailyLog（あれば）
        
        Returns:
            AI回答
        """
        # APIキーが設定されていない場合はフォールバック
        if not self.client:
            logger.warning("OpenAI API key not configured, using fallback response")
            return self._fallback_response(question, department.code)
        
        try:
            # System Promptを構築
            system_prompt = self._build_system_prompt(
                department.code,
                user.role,
                department.name
            )
            
            # コンテキストを構築
            context = self._build_context_from_logs(recent_logs, summary, today_log)
            
            # ユーザーメッセージを構築
            user_message = f"""
{context}

【質問】
{question}

上記の状況を踏まえて、DX参謀として以下の5つのセクションで回答してください：
1. 今日の状況の理解（どの経営課題／現場課題に紐づくか含む）
2. すぐにできる一手（明日から）- BPRの視点も含める
3. 小さな実験案（1〜2週間）- KPIと判断ライン、成功事例との対応関係を含む
4. 水平思考での一歩先の視点（他事業との連携・データ共有の視点を含む）
5. リスク・注意点（失敗パターン回避策を含む）

必ず、5つの観点（Whyの明確化、BPR、現場オーナーシップ、越境・横断の視点、持続可能性とガバナンス）を意識して回答してください。
"""
            
            # OpenAI APIを呼び出し
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000,  # DX参謀モードは詳細な回答のため増やす
            )
            
            answer = response.choices[0].message.content
            logger.info("AI answer generated", question_length=len(question), answer_length=len(answer))
            return answer
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e), exc_info=True)
            # エラー時もフォールバックで応答
            return self._fallback_response(question, department.code)
    
    def _fallback_response(
        self,
        question: str,
        department_code: str
    ) -> str:
        """
        OpenAI APIが使えない場合のフォールバック応答
        
        Args:
            question: ユーザーの質問
            department_code: 部署コード
        
        Returns:
            フォールバック応答
        """
        fallback_responses = {
            "coating": "コーティングの受注率向上のため、洗車からコーティングへの自然な流れを作ることが大切です。お客様の車の状態を見ながら、コーティングのメリットを具体的に説明してみてください。",
            "mnet": "来店されたお客様には、まずしっかりとヒアリングを行い、お客様のニーズを把握することが成約への第一歩です。在庫の特徴を活かした提案を心がけてください。",
            "gas": "給油のお客様には、洗車やコーティング、喫茶への自然な案内を心がけてください。声かけのタイミングが重要です。",
            "cafe": "お客様の滞在満足度を高めながら、適切な回転率を保つことが大切です。セットメニューやデザートの提案で客単価アップを目指しましょう。",
            "head": "部署横断でトレンドを把握し、KPIに基づいた施策を検討することが重要です。現場の声を大切にしながら、数字と肌感を結びつけましょう。",
        }
        
        base_response = fallback_responses.get(
            department_code,
            "ご質問ありがとうございます。具体的な状況を教えていただければ、より詳しいアドバイスができます。"
        )
        
        return f"{base_response}\n\n（注: AI機能の設定が完了していないため、一般的なアドバイスを表示しています。設定完了後は、より具体的なアドバイスが可能になります。）"
    
    async def get_suggestions(self, department_code: str) -> List[str]:
        """
        部署に応じた質問サジェストを取得
        
        Args:
            department_code: 部署コード
        
        Returns:
            サジェスト質問のリスト
        """
        suggestions_map = {
            "coating": [
                "コーティングの受注率を上げるには？",
                "洗車からコーティングへのアップセル方法は？",
                "納車時の説明で気をつけることは？",
            ],
            "mnet": [
                "来店から成約までの流れを改善するには？",
                "在庫回転率を上げるには？",
                "お客様との信頼関係を築くには？",
            ],
            "gas": [
                "給油客を洗車・コーティングに誘導するには？",
                "ピーク時間帯の効率的な動き方は？",
                "固定客を増やすには？",
            ],
            "cafe": [
                "客単価を上げるには？",
                "忙しい時間帯の回転率を上げるには？",
                "お客様に喜ばれる接客のコツは？",
            ],
            "head": [
                "部署横断で売上を上げるには？",
                "スタッフのモチベーションを上げるには？",
                "KPIを達成するための施策は？",
            ],
        }
        
        return suggestions_map.get(department_code, [
            "今日の接客のコツは？",
            "売上を上げるための工夫は？",
        ])

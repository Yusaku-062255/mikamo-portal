"""
AIサービス（v2: 抽象化レイヤー対応）

既存のAIServiceを新しいAiClient抽象化レイヤーを使うようにリファクタリング
システムプロンプトを外部ファイルから読み込む
"""
import os
from typing import Optional, List, Dict
from pathlib import Path
from app.core.config import settings
from app.models.daily_log import DailyLog
from app.models.user import Department, User
from app.services.ai.client import AiClientFactory
import structlog

logger = structlog.get_logger()


class AIServiceV2:
    """AI相談サービス - ミカモ専属DX参謀AI（v2: 抽象化レイヤー対応）"""
    
    def __init__(self):
        # AI Client Factoryを使用してプロバイダーに応じたClientを取得
        self.ai_client = AiClientFactory.create()
        self.system_prompt_path = Path(__file__).parent / "ai" / "system_prompts" / "mikamo_assistant_ja.md"
        self._system_prompt_cache: Optional[str] = None
    
    def _load_system_prompt(self) -> str:
        """
        システムプロンプトを外部ファイルから読み込む
        
        Returns:
            システムプロンプト文字列
        """
        if self._system_prompt_cache:
            return self._system_prompt_cache
        
        try:
            if self.system_prompt_path.exists():
                with open(self.system_prompt_path, "r", encoding="utf-8") as f:
                    self._system_prompt_cache = f.read()
                return self._system_prompt_cache
            else:
                logger.warning(f"System prompt file not found: {self.system_prompt_path}")
                return self._get_default_system_prompt()
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """デフォルトのシステムプロンプト（フォールバック）"""
        return """あなたは株式会社ミカモの社内アドバイザー／業務改善コンサルです。

5つの事業部門（ミカモ石油、カーコーティング、中古車販売、ミカモ喫茶、本部）の違いを理解した上で、
経営的に現実的な提案を行ってください。

回答は日本語で、です・ます調でお願いします。"""
    
    def _build_system_prompt_with_context(
        self,
        department_code: str,
        role: str,
        department_name: str
    ) -> str:
        """
        部署・ロールに応じたSystem Promptを構築（外部ファイルベース）
        
        Args:
            department_code: 部署コード
            role: ユーザーのロール
            department_name: 部署名
        
        Returns:
            System Prompt文字列
        """
        base_prompt = self._load_system_prompt()
        
        # 部署・ロール情報を追加
        context = f"""
現在のユーザー: {department_name}の{role}
事業部門コード: {department_code}
"""
        
        return base_prompt + context
    
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
        today_log: Optional[DailyLog] = None,
        knowledge_context: Optional[str] = None
    ) -> str:
        """
        AI回答を生成（抽象化レイヤー経由）
        
        Args:
            question: ユーザーの質問
            user: ユーザー情報
            department: 部署情報
            recent_logs: 直近のDailyLogリスト
            summary: サマリーデータ
            today_log: 今日のDailyLog（あれば）
            knowledge_context: ナレッジベースからの関連情報（あれば）
        
        Returns:
            AI回答
        """
        try:
            # System Promptを構築
            system_prompt = self._build_system_prompt_with_context(
                department.code,
                user.role,
                department.name
            )
            
            # コンテキストを構築
            context = self._build_context_from_logs(recent_logs, summary, today_log)
            
            # ナレッジベースからの情報を追加
            if knowledge_context:
                context += f"\n\n【関連ナレッジ情報】\n{knowledge_context}\n"
            
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

【重要】回答の最後に、必ず1つだけ短い質問かシンプルな行動提案を添えてください。
例：「ここまでで気になる点はありますか？」「もしよければ、今の店舗の具体的な状況も教えてください。」

【オプション】もしこの質問が「現場の困りごと・課題」として重要だと判断した場合、以下のJSON形式で追加情報を返してください：
```json
{{
  "issue_title": "課題の要約タイトル（100文字以内）",
  "issue_description": "課題の詳細説明",
  "issue_topic": "menu|operation|customer_complaint|future_risk|sales_opportunity|staffing|other",
  "insight_title": "提案・気付きの要約（重要度が高い場合のみ）",
  "insight_content": "提案・分析の詳細（重要度が高い場合のみ）",
  "insight_type": "risk|opportunity|improvement",
  "insight_score": 0-100の重要度スコア（60以上の場合のみ返す）
}}
```
"""
            
            # AI Clientを使用して応答を生成
            messages = [
                {"role": "user", "content": user_message}
            ]
            
            answer = await self.ai_client.generate_reply(
                system_prompt=system_prompt,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            logger.info("AI answer generated", question_length=len(question), answer_length=len(answer))
            return answer
            
        except Exception as e:
            logger.error("AI service error", error=str(e), exc_info=True)
            # エラー時もフォールバックで応答
            return self._fallback_response(question, department.code)
    
    def _fallback_response(
        self,
        question: str,
        department_code: str
    ) -> str:
        """
        AI APIが使えない場合のフォールバック応答
        
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
        
        return fallback_responses.get(
            department_code,
            "ご質問ありがとうございます。現在、AIサービスが利用できない状態です。しばらくしてから再度お試しください。"
        )
    
    async def get_suggestions(self, department_code: str) -> List[str]:
        """
        部署に応じた質問サジェストを取得
        
        Args:
            department_code: 部署コード
        
        Returns:
            サジェストリスト
        """
        suggestions_map = {
            "coating": [
                "コーティングの受注率を上げるには？",
                "洗車からコーティングへのアップセル方法は？",
                "施工品質を向上させるには？",
            ],
            "mnet": [
                "来店客の成約率を上げるには？",
                "在庫回転率を改善するには？",
                "お客様との信頼関係を築くには？",
            ],
            "gas": [
                "給油客を他のサービスに誘導するには？",
                "ピーク時間の回転率を上げるには？",
                "固定客を増やすには？",
            ],
            "cafe": [
                "客単価を上げるには？",
                "回転率と満足度のバランスを取るには？",
                "SNSで話題になる工夫は？",
            ],
            "head": [
                "部署横断で売上を上げるには？",
                "KPI設定のポイントは？",
                "全社的な業務改善の進め方は？",
            ],
        }
        
        return suggestions_map.get(department_code, [
            "今日の業務で改善できる点は？",
            "売上を上げるための工夫は？",
        ])


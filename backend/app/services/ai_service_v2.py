"""
AIサービス（v2: 抽象化レイヤー対応）

既存のAIServiceを新しいAiClient抽象化レイヤーを使うようにリファクタリング
システムプロンプトを外部ファイルから読み込む

SaaS対応: テナント設定からAIプロンプトを動的に取得
"""
from typing import Optional, List, Dict
from pathlib import Path
from sqlmodel import Session, select
from app.core.config import settings
from app.models.daily_log import DailyLog
from app.models.user import Department, User
from app.models.tenant import Tenant, TenantSettings
from app.services.ai.client import AiClientFactory
import structlog

logger = structlog.get_logger()


# デフォルトのシステムプロンプトテンプレート
# TenantSettings.ai_company_context が設定されている場合はそちらを優先
DEFAULT_SYSTEM_PROMPT_TEMPLATE = """あなたは{company_name}の社内アドバイザー／業務改善コンサルです。

事業部門の違いを理解した上で、経営的に現実的な提案を行ってください。

回答は日本語で、です・ます調でお願いします。"""


class AIServiceV2:
    """AI相談サービス - DX参謀AI（v2: 抽象化レイヤー対応、マルチテナント対応）"""

    def __init__(self, tenant_settings: Optional[TenantSettings] = None):
        """
        AIサービスを初期化

        Args:
            tenant_settings: テナント設定（ティアポリシー適用用）
        """
        # 用途を設定
        self._purpose = "management_decision"

        # テナントのティアポリシーを取得してAI Clientを作成
        if tenant_settings and tenant_settings.ai_tier_policy:
            # 経営判断用は "management_decision" 用途を使用
            self.ai_client = AiClientFactory.create_for_purpose_with_policy(
                self._purpose,
                tenant_settings.ai_tier_policy
            )
            # effective tierを計算して保存
            original_tier = AiClientFactory.get_tier_for_purpose(self._purpose)
            self._effective_tier = AiClientFactory.apply_tier_policy(
                original_tier,
                tenant_settings.ai_tier_policy
            ).value
        else:
            # デフォルト: AI Client Factoryを使用してプロバイダーに応じたClientを取得
            self.ai_client = AiClientFactory.create()
            self._effective_tier = AiClientFactory.get_tier_for_purpose(self._purpose).value

        # モデル名を保存（ログ用）
        self._model = getattr(self.ai_client, "model", "unknown")

        self.system_prompt_path = Path(__file__).parent / "ai" / "system_prompts" / "mikamo_assistant_ja.md"
        self._system_prompt_cache: Optional[str] = None
        self.tenant_settings = tenant_settings

    @property
    def purpose(self) -> str:
        """用途を取得"""
        return self._purpose

    @property
    def effective_tier(self) -> str:
        """ポリシー適用後のティアを取得"""
        return self._effective_tier

    @property
    def model_name(self) -> str:
        """使用モデル名を取得"""
        return self._model

    def _get_tenant_settings(self, session: Session, tenant_id: int) -> Optional[TenantSettings]:
        """
        テナント設定を取得

        Args:
            session: データベースセッション
            tenant_id: テナントID

        Returns:
            TenantSettingsオブジェクト（存在しない場合はNone）
        """
        statement = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        return session.exec(statement).first()

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
                return None  # テナント設定にフォールバック
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return None  # テナント設定にフォールバック

    def _get_default_system_prompt(self, company_name: str = "DXポータル") -> str:
        """
        デフォルトのシステムプロンプト（フォールバック）

        Args:
            company_name: 会社名（テナント設定から取得）
        """
        return DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(company_name=company_name)
    
    def _build_system_prompt_with_context(
        self,
        department_code: str,
        role: str,
        department_name: str,
        tenant_settings: Optional[TenantSettings] = None,
        company_name: str = "DXポータル"
    ) -> str:
        """
        部署・ロールに応じたSystem Promptを構築（外部ファイルベース、テナント設定対応）

        Args:
            department_code: 部署コード
            role: ユーザーのロール
            department_name: 部署名
            tenant_settings: テナント設定（オプション）
            company_name: 会社名（テナント設定がない場合のフォールバック）

        Returns:
            System Prompt文字列
        """
        # 1. 外部ファイルからシステムプロンプトを読み込む
        base_prompt = self._load_system_prompt()

        # 2. 外部ファイルがない場合、テナント設定またはデフォルトを使用
        if not base_prompt:
            if tenant_settings and tenant_settings.ai_company_context:
                base_prompt = tenant_settings.ai_company_context
            else:
                base_prompt = self._get_default_system_prompt(company_name)

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
        session: Session,
        question: str,
        user: User,
        department: Department,
        recent_logs: List[DailyLog],
        summary: Dict,
        today_log: Optional[DailyLog] = None,
        knowledge_context: Optional[str] = None
    ) -> str:
        """
        AI回答を生成（抽象化レイヤー経由、マルチテナント対応）

        Args:
            session: データベースセッション
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
            # テナント設定を取得（SaaS対応）
            tenant_settings = None
            company_name = "DXポータル"  # フォールバック
            if user.tenant_id:
                tenant_settings = self._get_tenant_settings(session, user.tenant_id)
                # テナントの表示名を取得
                tenant = session.get(Tenant, user.tenant_id)
                if tenant:
                    company_name = tenant.display_name

            logger.debug(
                "Building AI prompt",
                tenant_id=user.tenant_id,
                has_tenant_settings=tenant_settings is not None,
                company_name=company_name
            )

            # System Promptを構築（テナント設定を反映）
            system_prompt = self._build_system_prompt_with_context(
                department.code,
                user.role,
                department.name,
                tenant_settings=tenant_settings,
                company_name=company_name
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

        SaaS対応: テナント固有の内容は含まず、汎用的な応答を返す

        Args:
            question: ユーザーの質問
            department_code: 部署コード

        Returns:
            フォールバック応答
        """
        # 汎用的なフォールバック応答（テナント非依存）
        return (
            "ご質問ありがとうございます。現在、AIサービスが一時的に利用できない状態です。"
            "しばらくしてから再度お試しいただくか、管理者にお問い合わせください。"
        )
    
    async def get_suggestions(self, department_code: str) -> List[str]:
        """
        部署に応じた質問サジェストを取得

        SaaS対応: 汎用的な質問サジェストを提供

        Args:
            department_code: 部署コード

        Returns:
            サジェストリスト
        """
        # 汎用的なサジェスト（テナント非依存）
        # 将来的にはTenantSettingsで部門ごとのサジェストをカスタマイズ可能にする
        return [
            "今日の業務で改善できる点は？",
            "売上を上げるための工夫は？",
            "業務効率を向上させるには？",
        ]


"""
AI Client 抽象インターフェース

外部LLM APIを統一的なインターフェースで扱うための抽象化レイヤー
用途（Purpose）に応じて BASIC / STANDARD / PREMIUM の3段階ティアを自動選択
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Literal, TYPE_CHECKING
from enum import Enum
from app.core.config import settings
import structlog

if TYPE_CHECKING:
    from app.models.tenant import AiTierPolicy

logger = structlog.get_logger()


class AiTier(str, Enum):
    """AIモデルのティア（性能レベル）"""
    BASIC = "basic"       # 軽量・高速・低コスト
    STANDARD = "standard"  # バランス型
    PREMIUM = "premium"    # 高性能・高精度


# 用途（Purpose）からティア（Tier）へのマッピング
# キー: 用途名、バリュー: 使用するティア
PURPOSE_TO_TIER: Dict[str, AiTier] = {
    # BASIC: シフト管理、ログ要約など軽めのタスク
    "shift_planning": AiTier.BASIC,
    "log_summary": AiTier.BASIC,
    "simple_task": AiTier.BASIC,
    "schedule": AiTier.BASIC,

    # STANDARD: 従業員Q&A、ナレッジ検索など
    "staff_qa": AiTier.STANDARD,
    "knowledge_search": AiTier.STANDARD,
    "customer_support": AiTier.STANDARD,
    "daily_report": AiTier.STANDARD,
    "default": AiTier.STANDARD,  # デフォルト

    # PREMIUM: 経営判断、DXレポート分析など
    "management_decision": AiTier.PREMIUM,
    "dx_report": AiTier.PREMIUM,
    "strategic_planning": AiTier.PREMIUM,
    "executive_summary": AiTier.PREMIUM,
    "business_analysis": AiTier.PREMIUM,
}


class AiClient(ABC):
    """AI Client 抽象クラス"""

    @abstractmethod
    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict] = None
    ) -> str:
        """
        AIからの応答を生成

        Args:
            system_prompt: システムプロンプト
            messages: 会話履歴（[{"role": "user", "content": "..."}, ...]）
            options: 追加オプション（temperature, max_tokens等）

        Returns:
            AIからの応答テキスト
        """
        pass


class AiClientFactory:
    """AI Client ファクトリ（3段階ティア対応）"""

    @staticmethod
    def get_tier_for_purpose(purpose: str) -> AiTier:
        """
        用途からティアを決定

        Args:
            purpose: 用途名（"staff_qa", "management_decision" など）

        Returns:
            対応するティア
        """
        return PURPOSE_TO_TIER.get(purpose.lower(), AiTier.STANDARD)

    @staticmethod
    def get_tier_config(tier: AiTier) -> Dict:
        """
        ティアに応じた設定を取得

        Args:
            tier: ティア（BASIC, STANDARD, PREMIUM）

        Returns:
            model, max_tokens, temperature の設定
        """
        if tier == AiTier.BASIC:
            return {
                "model": settings.ANTHROPIC_MODEL_BASIC,
                "max_tokens": settings.ANTHROPIC_MAX_TOKENS_BASIC,
                "temperature": settings.ANTHROPIC_TEMPERATURE_BASIC,
            }
        elif tier == AiTier.STANDARD:
            return {
                "model": settings.ANTHROPIC_MODEL_STANDARD,
                "max_tokens": settings.ANTHROPIC_MAX_TOKENS_STANDARD,
                "temperature": settings.ANTHROPIC_TEMPERATURE_STANDARD,
            }
        else:  # PREMIUM
            return {
                "model": settings.ANTHROPIC_MODEL_PREMIUM,
                "max_tokens": settings.ANTHROPIC_MAX_TOKENS_PREMIUM,
                "temperature": settings.ANTHROPIC_TEMPERATURE_PREMIUM,
            }

    @staticmethod
    def create_for_purpose(purpose: str) -> "AiClient":
        """
        用途に応じたAI Clientを作成

        Args:
            purpose: 用途名（"staff_qa", "shift_planning", "management_decision" など）

        Returns:
            AiClientインスタンス（適切なティアで設定済み）
        """
        tier = AiClientFactory.get_tier_for_purpose(purpose)
        config = AiClientFactory.get_tier_config(tier)

        # モデルが設定されていない場合はエラー
        if not config["model"]:
            raise ValueError(
                f"AI model not configured for tier '{tier.value}'. "
                f"Please set ANTHROPIC_MODEL_{tier.value.upper()} environment variable."
            )

        # APIキーが設定されていない場合はエラー
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Please configure it via environment variable or Secret Manager."
            )

        logger.info(
            "Creating AI client",
            purpose=purpose,
            tier=tier.value,
            model=config["model"]
        )

        from app.services.ai.providers.anthropic_client import AnthropicClient
        return AnthropicClient(
            model=config["model"],
            default_max_tokens=config["max_tokens"],
            default_temperature=config["temperature"]
        )

    @staticmethod
    def create(provider: Optional[str] = None) -> AiClient:
        """
        【後方互換性】AIプロバイダーに応じたClientインスタンスを作成

        新規実装では create_for_purpose() を使用してください
        """
        if provider is None:
            provider = getattr(settings, "AI_PROVIDER", "anthropic").lower()

        if provider == "openai":
            from app.services.ai.providers.openai_client import OpenAiClient
            return OpenAiClient()
        elif provider == "cloud-code" or provider == "cloudcode":
            from app.services.ai.providers.cloud_code_client import CloudCodeAiClient
            return CloudCodeAiClient()
        elif provider == "anthropic":
            from app.services.ai.providers.anthropic_client import AnthropicClient
            # 後方互換性: STANDARD ティアの設定を使用
            model = settings.ANTHROPIC_MODEL_STANDARD or settings.AI_MODEL_STAFF
            return AnthropicClient(model=model)
        else:
            raise ValueError(f"Unknown AI provider: {provider}")

    @staticmethod
    def get_staff_client() -> AiClient:
        """
        【後方互換性】スタッフQA用の軽量モデルClientを取得

        新規実装では create_for_purpose("staff_qa") を使用してください
        """
        provider = getattr(settings, "AI_PROVIDER_STAFF", "anthropic").lower()

        if provider == "anthropic":
            # 新しいティア設定を優先、なければ旧設定を使用
            model = (
                settings.ANTHROPIC_MODEL_STANDARD or
                settings.AI_MODEL_STAFF or
                "claude-3-haiku-20240307"  # フォールバック
            )

            if not settings.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not set. "
                    "Please configure it via environment variable or Secret Manager."
                )

            logger.info("Creating staff QA client", model=model)

            from app.services.ai.providers.anthropic_client import AnthropicClient
            return AnthropicClient(
                model=model,
                default_max_tokens=settings.AI_MAX_TOKENS_STAFF,
                default_temperature=settings.AI_TEMPERATURE_STAFF
            )
        elif provider == "openai":
            from app.services.ai.providers.openai_client import OpenAiClient
            model_staff = getattr(settings, "AI_MODEL_STAFF", "gpt-4o-mini")
            return OpenAiClient(model=model_staff)
        elif provider == "cloud-code" or provider == "cloudcode":
            from app.services.ai.providers.cloud_code_client import CloudCodeAiClient
            model_staff = getattr(settings, "AI_MODEL_STAFF", "gpt-4o-mini")
            return CloudCodeAiClient(model=model_staff)
        else:
            raise ValueError(f"Unknown AI provider for staff QA: {provider}")

    @staticmethod
    def get_executive_client() -> AiClient:
        """
        経営判断用の高性能モデルClientを取得
        """
        return AiClientFactory.create_for_purpose("management_decision")

    @staticmethod
    def apply_tier_policy(tier: AiTier, tier_policy: "AiTierPolicy") -> AiTier:
        """
        テナントのティアポリシーを適用し、許可されたティアに制限する

        Args:
            tier: 用途から決定されたティア
            tier_policy: テナントのAIティアポリシー

        Returns:
            ポリシー適用後のティア（ダウングレードされる場合あり）
        """
        from app.models.tenant import AiTierPolicy

        if tier_policy == AiTierPolicy.ALL:
            # 全ティア利用可能 - そのまま返す
            return tier
        elif tier_policy == AiTierPolicy.STANDARD_MAX:
            # STANDARD以下のみ - PREMIUMはSTANDARDにダウングレード
            if tier == AiTier.PREMIUM:
                logger.info(
                    "Tier downgraded by policy",
                    original_tier=tier.value,
                    new_tier=AiTier.STANDARD.value,
                    policy=tier_policy.value
                )
                return AiTier.STANDARD
            return tier
        elif tier_policy == AiTierPolicy.BASIC_ONLY:
            # BASICのみ - 全てBASICにダウングレード
            if tier != AiTier.BASIC:
                logger.info(
                    "Tier downgraded by policy",
                    original_tier=tier.value,
                    new_tier=AiTier.BASIC.value,
                    policy=tier_policy.value
                )
                return AiTier.BASIC
            return tier
        else:
            # 不明なポリシー - 安全のためSTANDARDを返す
            logger.warning("Unknown tier policy", policy=tier_policy)
            return AiTier.STANDARD

    @staticmethod
    def create_for_purpose_with_policy(
        purpose: str,
        tier_policy: "AiTierPolicy"
    ) -> "AiClient":
        """
        用途とテナントポリシーに応じたAI Clientを作成

        Args:
            purpose: 用途名（"staff_qa", "management_decision" など）
            tier_policy: テナントのAIティアポリシー

        Returns:
            AiClientインスタンス（ポリシー適用後のティアで設定済み）
        """
        # 用途からティアを決定
        tier = AiClientFactory.get_tier_for_purpose(purpose)

        # テナントポリシーを適用
        effective_tier = AiClientFactory.apply_tier_policy(tier, tier_policy)

        # ティア設定を取得
        config = AiClientFactory.get_tier_config(effective_tier)

        # モデルが設定されていない場合はエラー
        if not config["model"]:
            raise ValueError(
                f"AI model not configured for tier '{effective_tier.value}'. "
                f"Please set ANTHROPIC_MODEL_{effective_tier.value.upper()} environment variable."
            )

        # APIキーが設定されていない場合はエラー
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Please configure it via environment variable or Secret Manager."
            )

        logger.info(
            "Creating AI client with tier policy",
            purpose=purpose,
            original_tier=tier.value,
            effective_tier=effective_tier.value,
            model=config["model"]
        )

        from app.services.ai.providers.anthropic_client import AnthropicClient
        return AnthropicClient(
            model=config["model"],
            default_max_tokens=config["max_tokens"],
            default_temperature=config["temperature"]
        )

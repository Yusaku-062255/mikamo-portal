"""
AI Client 抽象インターフェース

外部LLM APIを統一的なインターフェースで扱うための抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Literal
from app.core.config import settings


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
    """AI Client ファクトリ"""
    
    @staticmethod
    def create(provider: Optional[str] = None) -> AiClient:
        """
        AIプロバイダーに応じたClientインスタンスを作成（経営判断用・デフォルト）
        
        Args:
            provider: プロバイダー名（"openai", "cloud-code", "anthropic"等）
                     未指定の場合は環境変数 AI_PROVIDER から読み込む
        
        Returns:
            AiClientインスタンス
        """
        if provider is None:
            provider = getattr(settings, "AI_PROVIDER", "openai").lower()
        
        if provider == "openai":
            from app.services.ai.providers.openai_client import OpenAiClient
            return OpenAiClient()
        elif provider == "cloud-code" or provider == "cloudcode":
            from app.services.ai.providers.cloud_code_client import CloudCodeAiClient
            return CloudCodeAiClient()
        elif provider == "anthropic":
            from app.services.ai.providers.anthropic_client import AnthropicClient
            return AnthropicClient()
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    @staticmethod
    def get_staff_client() -> AiClient:
        """
        スタッフQA用の軽量モデルClientを取得
        
        環境変数 AI_PROVIDER_STAFF / AI_MODEL_STAFF を参照して、
        コスト最適化された軽量モデルを使用する
        
        Returns:
            AiClientインスタンス（軽量モデル設定）
        """
        provider = getattr(settings, "AI_PROVIDER_STAFF", "cloud-code").lower()
        
        if provider == "openai":
            from app.services.ai.providers.openai_client import OpenAiClient
            model_staff = getattr(settings, "AI_MODEL_STAFF", "gpt-4o-mini")
            return OpenAiClient(model=model_staff)
        elif provider == "cloud-code" or provider == "cloudcode":
            from app.services.ai.providers.cloud_code_client import CloudCodeAiClient
            model_staff = getattr(settings, "AI_MODEL_STAFF", "gpt-4o-mini")
            return CloudCodeAiClient(model=model_staff)
        elif provider == "anthropic":
            from app.services.ai.providers.anthropic_client import AnthropicClient
            model_staff = getattr(settings, "AI_MODEL_STAFF", "claude-3-haiku-20240307")
            return AnthropicClient(model=model_staff)
        else:
            raise ValueError(f"Unknown AI provider for staff QA: {provider}")
    
    @staticmethod
    def get_executive_client() -> AiClient:
        """
        経営判断用の高性能モデルClientを取得（将来実装用プレースホルダ）
        
        現時点では実装していないが、将来の拡張を見据えた設計
        
        Returns:
            AiClientインスタンス（高性能モデル設定）
        """
        # TODO: 将来実装
        # provider = getattr(settings, "AI_PROVIDER_EXECUTIVE", "openai").lower()
        # ...
        raise NotImplementedError("Executive client is not yet implemented")


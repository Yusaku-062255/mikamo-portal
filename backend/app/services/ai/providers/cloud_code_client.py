"""
Cloud Code API Client 実装

将来的にCloud Code APIを使用する場合の実装
"""
from typing import List, Dict, Optional
import httpx
from app.core.config import settings
from app.services.ai.client import AiClient
import structlog

logger = structlog.get_logger()


class CloudCodeAiClient(AiClient):
    """Cloud Code API Client"""
    
    def __init__(self, model: Optional[str] = None):
        self.api_key = getattr(settings, "AI_API_KEY", None)
        self.api_base_url = getattr(settings, "AI_API_BASE_URL", None)
        # モデル名は引数で指定可能（スタッフQA用など）
        self.model = model or getattr(settings, "AI_MODEL", "gpt-4o-mini")
        
        if not self.api_base_url:
            logger.warning("AI_API_BASE_URL not set, Cloud Code client will not work")
    
    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict] = None
    ) -> str:
        """
        Cloud Code APIを使用して応答を生成
        
        Args:
            system_prompt: システムプロンプト
            messages: 会話履歴
            options: 追加オプション
        
        Returns:
            AIからの応答テキスト
        """
        if not self.api_base_url:
            raise ValueError("AI_API_BASE_URL is not set")
        
        # システムプロンプトをメッセージリストの先頭に追加
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        # Cloud Code APIのリクエスト形式に合わせて構築
        # （実際のAPI仕様に応じて調整が必要）
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": options.get("temperature", 0.7) if options else 0.7,
            "max_tokens": options.get("max_tokens", 2000) if options else 2000
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Cloud Code API error", error=str(e))
            raise


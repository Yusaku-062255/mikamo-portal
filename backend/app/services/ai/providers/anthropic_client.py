"""
Anthropic (Claude) API Client 実装

Claude APIを使用して応答を生成するクライアント
"""
from typing import List, Dict, Optional
import httpx
from app.core.config import settings
from app.services.ai.client import AiClient
import structlog

logger = structlog.get_logger()


class AnthropicClient(AiClient):
    """Anthropic (Claude) API Client"""
    
    def __init__(self, model: Optional[str] = None):
        self.api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        self.api_base_url = getattr(settings, "ANTHROPIC_API_BASE_URL", None) or "https://api.anthropic.com/v1/messages"
        # モデル名は引数で指定可能（スタッフQA用など）
        self.model = model or getattr(settings, "AI_MODEL_STAFF", "claude-3-haiku-20240307")
        
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set, Anthropic client will not work")
    
    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict] = None
    ) -> str:
        """
        Anthropic (Claude) APIを使用して応答を生成
        
        Args:
            system_prompt: システムプロンプト
            messages: 会話履歴（[{"role": "user", "content": "..."}, ...]）
            options: 追加オプション（temperature, max_tokens等）
        
        Returns:
            AIからの応答テキスト
        """
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        
        # Anthropic APIのリクエスト形式に合わせて構築
        # 参考: https://docs.anthropic.com/claude/reference/messages-post
        payload = {
            "model": self.model,
            "max_tokens": options.get("max_tokens", 1000) if options else 1000,
            "messages": messages,  # Anthropic APIはシステムプロンプトを別フィールドで扱う
            "system": system_prompt  # システムプロンプトは system フィールドに
        }
        
        # temperature が指定されている場合は追加
        if options and "temperature" in options:
            payload["temperature"] = options["temperature"]
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",  # Anthropic APIのバージョン
            "content-type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_base_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Anthropic APIのレスポンス形式: content[0].text
                if "content" in data and len(data["content"]) > 0:
                    return data["content"][0]["text"]
                else:
                    logger.error("Unexpected Anthropic API response format", response=data)
                    raise ValueError("Unexpected response format from Anthropic API")
                    
        except httpx.HTTPStatusError as e:
            logger.error("Anthropic API HTTP error", status_code=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise


"""
OpenAI Client 実装
"""
from typing import List, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.ai.client import AiClient
import structlog

logger = structlog.get_logger()


class OpenAiClient(AiClient):
    """OpenAI API Client"""
    
    def __init__(self, model: Optional[str] = None):
        self.client = None
        # 後方互換性のため、OPENAI_API_KEYもチェック
        self.api_key = getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "AI_API_KEY", None)
        # モデル名は引数で指定可能（スタッフQA用など）
        self.model = model or getattr(settings, "AI_MODEL", None) or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not set, OpenAI client will not work")
    
    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict] = None
    ) -> str:
        """
        OpenAI APIを使用して応答を生成
        
        Args:
            system_prompt: システムプロンプト
            messages: 会話履歴
            options: 追加オプション（temperature, max_tokens等）
        
        Returns:
            AIからの応答テキスト
        """
        if not self.client:
            raise ValueError("OpenAI API key is not set")
        
        # システムプロンプトをメッセージリストの先頭に追加
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        # オプションのデフォルト値
        temperature = options.get("temperature", 0.7) if options else 0.7
        max_tokens = options.get("max_tokens", 2000) if options else 2000
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise


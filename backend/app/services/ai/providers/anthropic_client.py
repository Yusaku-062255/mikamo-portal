"""
Anthropic (Claude) API Client 実装

Claude APIを使用して応答を生成するクライアント
3段階ティア（BASIC / STANDARD / PREMIUM）に対応
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx
from app.core.config import settings
from app.services.ai.client import AiClient
import structlog

logger = structlog.get_logger()


@dataclass
class AiResponse:
    """AI応答とメタデータを格納するデータクラス"""
    content: str
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    model: Optional[str] = None


class AnthropicClient(AiClient):
    """Anthropic (Claude) API Client"""

    def __init__(
        self,
        model: Optional[str] = None,
        default_max_tokens: int = 1000,
        default_temperature: float = 0.5
    ):
        """
        Anthropic Clientを初期化

        Args:
            model: 使用するモデル名（未指定時は設定から取得）
            default_max_tokens: デフォルトの最大トークン数
            default_temperature: デフォルトの温度パラメータ
        """
        self.api_key = settings.ANTHROPIC_API_KEY
        self.api_base_url = settings.ANTHROPIC_API_BASE_URL or "https://api.anthropic.com/v1/messages"
        self.model = model or settings.ANTHROPIC_MODEL_STANDARD or "claude-3-haiku-20240307"
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self._last_response: Optional[AiResponse] = None

        if not self.api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not set",
                hint="Set ANTHROPIC_API_KEY environment variable or configure Secret Manager"
            )

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

        Raises:
            ValueError: APIキーが設定されていない場合
            httpx.HTTPStatusError: API呼び出しでエラーが発生した場合
        """
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Please configure it via environment variable or Secret Manager (MIKAMO_ANTHROPIC_KEY)."
            )

        # オプションからパラメータを取得（デフォルト値を使用）
        max_tokens = (options.get("max_tokens") if options else None) or self.default_max_tokens
        temperature = (options.get("temperature") if options else None) or self.default_temperature

        # コスト管理: max_tokensの上限を設定（異常な消費を防ぐ）
        MAX_TOKENS_LIMIT = 8000
        if max_tokens > MAX_TOKENS_LIMIT:
            logger.warning(
                "max_tokens exceeds limit, capping",
                requested=max_tokens,
                limit=MAX_TOKENS_LIMIT
            )
            max_tokens = MAX_TOKENS_LIMIT

        # Anthropic APIのリクエスト形式に合わせて構築
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "system": system_prompt
        }

        # temperatureが指定されている場合は追加
        if temperature is not None:
            payload["temperature"] = temperature

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        logger.info(
            "Calling Anthropic API",
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            message_count=len(messages)
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_base_url,
                    json=payload,
                    headers=headers,
                    timeout=60.0  # タイムアウトを60秒に延長
                )
                response.raise_for_status()
                data = response.json()

                # Anthropic APIのレスポンス形式: content[0].text
                if "content" in data and len(data["content"]) > 0:
                    answer = data["content"][0]["text"]
                    usage = data.get("usage", {})
                    logger.info(
                        "Anthropic API response received",
                        model=self.model,
                        response_length=len(answer),
                        usage=usage
                    )

                    # 最後のレスポンスメタデータを保存（ログ記録用）
                    self._last_response = AiResponse(
                        content=answer,
                        tokens_input=usage.get("input_tokens"),
                        tokens_output=usage.get("output_tokens"),
                        model=self.model
                    )

                    return answer
                else:
                    logger.error("Unexpected Anthropic API response format", response=data)
                    raise ValueError("Unexpected response format from Anthropic API")

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = error_body.get("error", {}).get("message", str(e))
            except Exception:
                error_detail = str(e)

            logger.error(
                "Anthropic API HTTP error",
                status_code=e.response.status_code,
                error=error_detail,
                model=self.model
            )

            # エラーメッセージをより詳細に
            if e.response.status_code == 401:
                raise ValueError(
                    "Anthropic API authentication failed. "
                    "Please check ANTHROPIC_API_KEY is correctly set."
                ) from e
            elif e.response.status_code == 429:
                raise ValueError(
                    "Anthropic API rate limit exceeded. "
                    "Please try again later."
                ) from e
            elif e.response.status_code == 400:
                raise ValueError(
                    f"Anthropic API bad request: {error_detail}"
                ) from e
            else:
                raise

        except httpx.TimeoutException as e:
            logger.error("Anthropic API timeout", model=self.model)
            raise ValueError(
                "Anthropic API request timed out. "
                "The AI service may be experiencing high load."
            ) from e

        except Exception as e:
            logger.error("Anthropic API error", error=str(e), model=self.model)
            raise

    def get_last_response_metadata(self) -> Optional[AiResponse]:
        """
        最後のAPI呼び出しのメタデータを取得

        Returns:
            AiResponse: 応答内容とトークン使用量を含むオブジェクト
            呼び出し履歴がない場合はNone
        """
        return self._last_response

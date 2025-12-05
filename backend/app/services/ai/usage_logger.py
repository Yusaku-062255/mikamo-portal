"""
AI利用ログ記録ヘルパー

StaffQAService, AIServiceV2 などから呼び出され、
AI呼び出しの詳細をDBに記録する。

用途:
- コスト可視化
- テナント別・用途別の利用分析
- 将来の従量課金設計

使用例:
    from app.services.ai.usage_logger import log_ai_usage

    # AI呼び出し前に開始時刻を記録
    start_time = time.time()

    # AI呼び出し
    response = await ai_client.generate_reply(...)

    # ログを記録
    log_ai_usage(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        purpose="staff_qa",
        tier="standard",
        model="claude-3-sonnet-20240229",
        tokens_input=100,
        tokens_output=200,
        response_time_ms=int((time.time() - start_time) * 1000)
    )
"""
from typing import Optional
from sqlmodel import Session
from datetime import datetime
import structlog

logger = structlog.get_logger()


def log_ai_usage(
    session: Session,
    tenant_id: int,
    purpose: str,
    tier: str,
    model: str,
    user_id: Optional[int] = None,
    business_unit_id: Optional[int] = None,
    tokens_input: Optional[int] = None,
    tokens_output: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    error: Optional[str] = None,
    conversation_id: Optional[int] = None,
) -> None:
    """
    AI利用ログをDBに記録する

    Args:
        session: DBセッション
        tenant_id: テナントID（必須）
        purpose: 用途（"staff_qa", "management_decision" など）
        tier: 使用ティア（"basic", "standard", "premium"）
        model: 使用モデル名
        user_id: ユーザーID（オプション）
        business_unit_id: 事業部門ID（オプション）
        tokens_input: 入力トークン数（オプション）
        tokens_output: 出力トークン数（オプション）
        response_time_ms: 応答時間ミリ秒（オプション）
        error: エラーメッセージ（失敗時のみ）
        conversation_id: 会話ID（オプション）

    注意:
        - この関数はトランザクション内で呼び出されることを想定
        - 呼び出し元でcommitする必要がある
        - ログ記録自体の失敗は例外を投げず、警告ログのみ出力
    """
    try:
        from app.models.ai_usage_log import AiUsageLog

        usage_log = AiUsageLog(
            tenant_id=tenant_id,
            user_id=user_id,
            business_unit_id=business_unit_id,
            purpose=purpose,
            tier=tier,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            error=error,
            conversation_id=conversation_id,
        )
        session.add(usage_log)

        logger.info(
            "AI usage logged",
            tenant_id=tenant_id,
            user_id=user_id,
            purpose=purpose,
            tier=tier,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            has_error=error is not None,
        )

    except Exception as e:
        # ログ記録の失敗はAI機能を止めない（警告のみ）
        logger.warning(
            "Failed to log AI usage",
            error=str(e),
            tenant_id=tenant_id,
            purpose=purpose,
        )


def log_ai_usage_error(
    session: Session,
    tenant_id: int,
    purpose: str,
    tier: str,
    model: str,
    error_message: str,
    user_id: Optional[int] = None,
    business_unit_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> None:
    """
    AI呼び出しエラーをログに記録する

    Args:
        session: DBセッション
        tenant_id: テナントID
        purpose: 用途
        tier: 使用予定だったティア
        model: 使用予定だったモデル名
        error_message: エラーメッセージ（100文字まで切り詰め）
        user_id: ユーザーID（オプション）
        business_unit_id: 事業部門ID（オプション）
        conversation_id: 会話ID（オプション）
    """
    # エラーメッセージを短く切り詰め（スタックトレースは含めない）
    truncated_error = error_message[:200] if error_message else "Unknown error"

    log_ai_usage(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        business_unit_id=business_unit_id,
        purpose=purpose,
        tier=tier,
        model=model,
        error=truncated_error,
        conversation_id=conversation_id,
    )

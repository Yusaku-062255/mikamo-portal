"""
AIチャットAPI（v2: ナレッジ連携・会話履歴対応）

既存のエンドポイントは後方互換性のため残しつつ、
新しい会話履歴管理機能を追加
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List, Optional
from datetime import datetime
from app.core.database import get_session
from app.models.ai_chat_log import AIChatLog
from app.models.user import User, Department
from app.models.conversation import Conversation, Message
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user, get_current_user_with_department
from app.services.ai_service import AIService  # 既存（後方互換性）
from app.services.ai_service_v2 import AIServiceV2  # 新規（ナレッジ連携対応）
from app.repositories.daily_log_repository import (
    get_recent_daily_logs_by_department,
    get_daily_logs_summary_by_department,
    get_today_daily_log
)
from app.repositories.knowledge_repository import get_knowledge_context
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter()


# 既存のリクエスト/レスポンスモデル（後方互換性）
class AIChatRequest(BaseModel):
    question: str


class AIChatResponse(BaseModel):
    id: int
    user_id: int
    question: str
    answer: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# 新しいリクエスト/レスポンスモデル（v2）
class AIChatRequestV2(BaseModel):
    """AIチャットリクエスト（v2: 会話履歴対応）"""
    message: str  # ユーザーのメッセージ
    conversation_id: Optional[int] = None  # 既存の会話ID（新規会話の場合はNone）
    business_unit_id: Optional[int] = None  # 事業部門ID（未指定の場合はユーザーの所属部門）
    mode: Optional[str] = None  # "staff_qa" または None（デフォルトは通常モード）


class AIChatResponseV2(BaseModel):
    """AIチャットレスポンス（v2: 会話履歴対応）"""
    conversation_id: int
    reply: str  # AIからの応答
    message_id: int  # 作成されたメッセージID

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """会話レスポンス"""
    id: int
    title: Optional[str] = None
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    id: int
    role: str  # "user" or "assistant"
    content: str
    created_at: str

    class Config:
        from_attributes = True


# 既存のエンドポイント（後方互換性のため残す）
@router.post("", response_model=AIChatResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_chat(
    chat_data: AIChatRequest,
    user_dept: tuple[User, Department] = Depends(get_current_user_with_department),
    session: Session = Depends(get_session)
):
    """AI相談ログを作成（v0.2: OpenAI API統合、コンテキスト付き回答）"""
    current_user, department = user_dept
    
    # コンテキストデータを取得
    recent_logs = get_recent_daily_logs_by_department(
        session, department.id, days=14
    )
    summary = get_daily_logs_summary_by_department(
        session, department.id, days=14
    )
    today_log = get_today_daily_log(session, current_user.id)
    
    # AIサービスで回答を生成
    ai_service = AIService()
    answer = await ai_service.generate_answer(
        question=chat_data.question,
        user=current_user,
        department=department,
        recent_logs=recent_logs,
        summary=summary,
        today_log=today_log
    )
    
    chat_log = AIChatLog(
        user_id=current_user.id,
        question=chat_data.question,
        answer=answer
    )
    session.add(chat_log)
    session.commit()
    session.refresh(chat_log)
    return chat_log


# 新しいエンドポイント（v2: ナレッジ連携・会話履歴対応）
@router.post("/chat", response_model=AIChatResponseV2, status_code=status.HTTP_201_CREATED)
async def create_ai_chat_v2(
    chat_data: AIChatRequestV2,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    AIチャット（v2: ナレッジ連携・会話履歴対応）
    
    フロー:
    1. 会話IDがあれば既存会話、なければ新規会話を作成
    2. ナレッジベースから関連情報を検索
    3. 日報データからコンテキストを構築
    4. AI Clientで応答を生成
    5. 会話履歴に保存
    """
    # テナントIDを取得
    tenant_id = current_user.tenant_id
    if not tenant_id:
        from app.models.tenant import Tenant
        statement = select(Tenant).where(Tenant.name == "mikamo")
        tenant = session.exec(statement).first()
        if tenant:
            tenant_id = tenant.id
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="テナントが見つかりません"
            )
    
    # 事業部門を取得
    business_unit_id = chat_data.business_unit_id
    department = None
    if not business_unit_id:
        # 未指定の場合はユーザーの所属部門を使用
        business_unit_id = current_user.business_unit_id
        if not business_unit_id:
            # 後方互換性のため、Departmentもチェック
            department = session.get(Department, current_user.department_id)
            if department:
                # DepartmentのcodeからBusinessUnitを検索
                statement = select(BusinessUnit).where(BusinessUnit.code == department.code)
                business_unit = session.exec(statement).first()
                if business_unit:
                    business_unit_id = business_unit.id
    
    business_unit = None
    if business_unit_id:
        business_unit = session.get(BusinessUnit, business_unit_id)
        if not business_unit:
            # 後方互換性のため、Departmentもチェック
            department = session.get(Department, business_unit_id)
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="事業部門が見つかりません"
                )
    
    # 会話を取得または作成
    conversation = None
    if chat_data.conversation_id:
        conversation = session.get(Conversation, chat_data.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会話が見つかりません"
            )
    else:
        # 新規会話を作成
        conversation = Conversation(
            tenant_id=tenant_id,
            user_id=current_user.id,
            business_unit_id=business_unit_id if business_unit else None,
            title=chat_data.message[:50]  # 最初の50文字をタイトルに
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    
    # 既存の会話履歴を取得
    statement = select(Message).where(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc())
    existing_messages = session.exec(statement).all()
    
    # 会話履歴を構築（AI Client用の形式）
    messages = []
    for msg in existing_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # ユーザーメッセージを追加
    messages.append({
        "role": "user",
        "content": chat_data.message
    })
    
    # ナレッジベースから関連情報を検索
    knowledge_context = get_knowledge_context(
        session,
        query=chat_data.message,
        business_unit_id=business_unit_id,
        limit=3
    )
    
    # 日報データからコンテキストを構築
    department_for_logs = department or (business_unit and session.exec(
        select(Department).where(Department.code == business_unit.code)
    ).first())
    
    if department_for_logs:
        recent_logs = get_recent_daily_logs_by_department(
            session, department_for_logs.id, days=14
        )
        summary = get_daily_logs_summary_by_department(
            session, department_for_logs.id, days=14
        )
        today_log = get_today_daily_log(session, current_user.id)
    else:
        recent_logs = []
        summary = {}
        today_log = None
    
    # スタッフQAモードかどうかを判定
    use_staff_qa = False
    if chat_data.mode == "staff_qa":
        use_staff_qa = True
    elif current_user.role in ["staff", "manager"]:
        # スタッフ・マネージャーの場合はデフォルトでスタッフQAモード
        use_staff_qa = True
    
    # AI利用ログ用の変数
    ai_purpose = None
    ai_tier = None
    ai_model = None
    ai_tokens_input = None
    ai_tokens_output = None
    ai_error = None

    # スタッフQAモードの場合は軽量モデルを使用
    if use_staff_qa:
        from app.services.staff_qa_service import StaffQAService
        from app.models.tenant import TenantSettings
        try:
            # テナント設定を取得（ティアポリシー適用用）
            tenant_settings = None
            if tenant_id:
                stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
                tenant_settings = session.exec(stmt).first()

            staff_qa_service = StaffQAService(tenant_settings=tenant_settings)

            # ログ用にメタデータを保存
            ai_purpose = staff_qa_service.purpose
            ai_tier = staff_qa_service.effective_tier
            ai_model = staff_qa_service.model_name

            answer = await staff_qa_service.answer_staff_question(
                session=session,
                user=current_user,
                business_unit=business_unit,
                user_question=chat_data.message,
                conversation_id=conversation.id if conversation else None
            )

            # トークン使用量を取得（AnthropicClientの場合）
            if hasattr(staff_qa_service.ai_client, 'get_last_response_metadata'):
                metadata = staff_qa_service.ai_client.get_last_response_metadata()
                if metadata:
                    ai_tokens_input = metadata.tokens_input
                    ai_tokens_output = metadata.tokens_output

        except ValueError as e:
            error_msg = str(e)
            ai_error = error_msg[:200]  # エラーログ用
            # エラーコード:メッセージ の形式でパース
            if ":" in error_msg:
                error_code, message = error_msg.split(":", 1)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error_code": error_code,
                        "message": message
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "ai_error",
                        "message": error_msg
                    }
                )
    else:
        # 通常モード（経営判断用・デフォルト）
        # テナント設定を取得（ティアポリシー適用用）
        from app.models.tenant import TenantSettings as TS
        tenant_settings_for_ai = None
        if tenant_id:
            stmt = select(TS).where(TS.tenant_id == tenant_id)
            tenant_settings_for_ai = session.exec(stmt).first()

        ai_service = AIServiceV2(tenant_settings=tenant_settings_for_ai)

        # ログ用にメタデータを保存
        ai_purpose = ai_service.purpose
        ai_tier = ai_service.effective_tier
        ai_model = ai_service.model_name

        # Departmentオブジェクトを構築（既存のAIServiceV2のインターフェースに合わせる）
        dept_obj = department
        if not dept_obj and business_unit:
            # BusinessUnitからDepartmentを取得または作成
            dept_obj = session.exec(
                select(Department).where(Department.code == business_unit.code)
            ).first()
            if not dept_obj:
                # フォールバック: 仮のDepartmentオブジェクトを作成
                dept_obj = Department(name=business_unit.name, code=business_unit.code)

        answer = await ai_service.generate_answer(
            session=session,  # SaaS対応: テナント設定取得用
            question=chat_data.message,
            user=current_user,
            department=dept_obj,
            recent_logs=recent_logs,
            summary=summary,
            today_log=today_log,
            knowledge_context=knowledge_context if knowledge_context else None
        )

        # トークン使用量を取得（AnthropicClientの場合）
        if hasattr(ai_service.ai_client, 'get_last_response_metadata'):
            metadata = ai_service.ai_client.get_last_response_metadata()
            if metadata:
                ai_tokens_input = metadata.tokens_input
                ai_tokens_output = metadata.tokens_output

    # AI利用ログを記録
    from app.services.ai.usage_logger import log_ai_usage
    if ai_purpose and ai_tier and ai_model:
        log_ai_usage(
            session=session,
            tenant_id=tenant_id,
            user_id=current_user.id,
            business_unit_id=business_unit_id if business_unit else None,
            purpose=ai_purpose,
            tier=ai_tier,
            model=ai_model,
            tokens_input=ai_tokens_input,
            tokens_output=ai_tokens_output,
            error=ai_error,
            conversation_id=conversation.id if conversation else None,
        )
    
    # メッセージを保存
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_data.message
    )
    session.add(user_message)
    
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer
    )
    session.add(assistant_message)
    
    # 会話の更新日時を更新
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    
    # AIレスポンスからIssue/Insightを抽出・作成
    from app.services.issue_insight_extractor import extract_issue_insight_from_ai_response
    from app.models.issue import Issue, IssueStatus
    from app.models.insight import Insight
    
    extracted = extract_issue_insight_from_ai_response(answer, chat_data.message)
    
    # Issueを作成（重要度が高い場合のみ）
    if extracted.get("issue"):
        issue_data = extracted["issue"]
        # 既に同じようなIssueが存在しないかチェック（簡易版）
        existing_issue = session.exec(
            select(Issue).where(
                Issue.business_unit_id == business_unit_id if business_unit else None,
                or_(
                    Issue.title.contains(issue_data["title"][:50]),
                    Issue.description.contains(issue_data["description"][:100])
                )
            )
        ).first()
        
        if not existing_issue:
            issue = Issue(
                tenant_id=tenant_id,
                business_unit_id=business_unit_id if business_unit else None,
                title=issue_data["title"],
                description=issue_data["description"],
                status=IssueStatus.OPEN,
                topic=issue_data["topic"],
                created_by_user_id=current_user.id,
                conversation_id=conversation.id
            )
            session.add(issue)
            logger.info("Issue created from AI response", issue_id=issue.id, conversation_id=conversation.id)
    
    # Insightを作成（重要度スコアが60以上の場合のみ）
    if extracted.get("insight") and extracted["insight"]["score"] >= 60:
        insight_data = extracted["insight"]
        insight = Insight(
            tenant_id=tenant_id,
            business_unit_id=business_unit_id if business_unit else None,
            title=insight_data["title"],
            content=insight_data["content"],
            type=insight_data["type"],
            score=insight_data["score"],
            created_by=None  # AIが作成
        )
        session.add(insight)
        logger.info("Insight created from AI response", insight_id=insight.id, score=insight.score)
    
    session.commit()
    session.refresh(assistant_message)
    
    return AIChatResponseV2(
        conversation_id=conversation.id,
        reply=answer,
        message_id=assistant_message.id
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """会話一覧を取得"""
    statement = select(Conversation).where(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
    conversations = session.exec(statement).all()
    
    result = []
    for conv in conversations:
        # メッセージ数を取得
        msg_statement = select(Message).where(Message.conversation_id == conv.id)
        msg_count = len(session.exec(msg_statement).all())
        
        business_unit = None
        if conv.business_unit_id:
            business_unit = session.get(BusinessUnit, conv.business_unit_id)
        
        result.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            business_unit_id=conv.business_unit_id,
            business_unit_name=business_unit.name if business_unit else None,
            created_at=conv.created_at.isoformat() if conv.created_at else "",
            updated_at=conv.updated_at.isoformat() if conv.updated_at else "",
            message_count=msg_count
        ))
    
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """会話のメッセージ一覧を取得"""
    conversation = session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つかりません"
        )
    
    statement = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc())
    messages = session.exec(statement).all()
    
    return [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat() if msg.created_at else ""
        )
        for msg in messages
    ]


@router.get("/logs", response_model=List[AIChatResponse])
async def get_ai_chat_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """AI相談ログ一覧を取得（後方互換性のため残す）"""
    statement = select(AIChatLog).where(
        AIChatLog.user_id == current_user.id
    ).order_by(AIChatLog.created_at.desc()).offset(skip).limit(limit)
    logs = session.exec(statement).all()
    return logs


@router.get("/{log_id}", response_model=AIChatResponse)
async def get_ai_chat_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """AI相談ログを取得"""
    statement = select(AIChatLog).where(
        AIChatLog.id == log_id,
        AIChatLog.user_id == current_user.id
    )
    log = session.exec(statement).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ログが見つかりません"
        )
    return log


@router.get("/suggestions", response_model=List[str])
async def get_suggestions(
    user_dept: tuple[User, Department] = Depends(get_current_user_with_department)
):
    """部署に応じた質問サジェストを取得"""
    current_user, department = user_dept
    ai_service = AIService()
    suggestions = await ai_service.get_suggestions(department.code)
    return suggestions


class AIHealthResponse(BaseModel):
    """AIヘルスチェックレスポンス"""
    status: str  # "healthy", "degraded", "unhealthy"
    provider: str  # "anthropic", "openai", "cloud-code"
    model: str
    message: str
    response_time_ms: Optional[float] = None


class AIErrorResponse(BaseModel):
    """AIエラーレスポンス（設定不足など）"""
    error_code: str  # "ai_not_configured", "ai_rate_limited", "ai_error"
    message: str
    detail: Optional[str] = None


@router.get("/health", response_model=AIHealthResponse)
async def check_ai_health():
    """
    AI（スタッフQA用）のヘルスチェック

    Anthropic API に軽量なテストリクエストを送信し、
    設定ミスやAPIキーの問題を早期に検出します。

    認証不要（デプロイ時の動作確認用）
    """
    from app.core.config import settings
    from app.services.ai.client import AiClientFactory
    import time

    provider = getattr(settings, "AI_PROVIDER_STAFF", "anthropic")
    model = getattr(settings, "AI_MODEL_STAFF", "claude-3-haiku-20240307")

    try:
        start_time = time.time()

        # スタッフQA用クライアントを取得
        client = AiClientFactory.get_staff_client()

        # 軽量なテストリクエスト（最小限のトークンで）
        response = await client.generate_reply(
            system_prompt="You are a test assistant. Respond with exactly 'OK' and nothing else.",
            messages=[{"role": "user", "content": "test"}],
            options={"max_tokens": 10, "temperature": 0}
        )

        elapsed_ms = (time.time() - start_time) * 1000

        if response and len(response.strip()) > 0:
            return AIHealthResponse(
                status="healthy",
                provider=provider,
                model=model,
                message=f"AI service is responding normally",
                response_time_ms=round(elapsed_ms, 2)
            )
        else:
            return AIHealthResponse(
                status="degraded",
                provider=provider,
                model=model,
                message="AI service responded but with empty content"
            )

    except ValueError as e:
        # API キーが設定されていないなどの設定エラー
        return AIHealthResponse(
            status="unhealthy",
            provider=provider,
            model=model,
            message=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error("AI health check failed", error=str(e), provider=provider)
        return AIHealthResponse(
            status="unhealthy",
            provider=provider,
            model=model,
            message=f"AI service error: {str(e)}"
        )

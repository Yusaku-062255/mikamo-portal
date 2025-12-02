from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from app.core.database import get_session
from app.models.ai_chat_log import AIChatLog
from app.models.user import User, Department
from app.api.deps import get_current_user, get_current_user_with_department
from app.services.ai_service import AIService
from app.repositories.daily_log_repository import (
    get_recent_daily_logs_by_department,
    get_daily_logs_summary_by_department,
    get_today_daily_log
)
from pydantic import BaseModel

router = APIRouter()


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


@router.get("", response_model=List[AIChatResponse])
async def get_ai_chat_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """AI相談ログ一覧を取得"""
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


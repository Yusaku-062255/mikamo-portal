"""
Decision API

経営・マネージャー側の意思決定ログを管理するAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.models.decision import Decision, DecisionStatus
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user, require_role
from datetime import datetime

router = APIRouter()


class DecisionCreate(BaseModel):
    """Decision作成リクエスト"""
    title: str
    content: str
    business_unit_id: Optional[int] = None
    related_insight_ids: Optional[List[int]] = None


class DecisionUpdate(BaseModel):
    """Decision更新リクエスト"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[DecisionStatus] = None


class DecisionResponse(BaseModel):
    """Decisionレスポンス"""
    id: int
    tenant_id: int
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    title: str
    content: str
    status: str
    created_by_user_id: int
    created_by_name: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[DecisionResponse])
async def list_decisions(
    business_unit_id: Optional[int] = Query(None, description="事業部門IDで絞り込み"),
    status: Optional[DecisionStatus] = Query(None, description="ステータスで絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    Decision一覧を取得

    権限: head/admin のみ
    """
    statement = select(Decision)
    
    # テナントで絞り込み
    if current_user.tenant_id:
        statement = statement.where(Decision.tenant_id == current_user.tenant_id)
    
    # フィルター
    if business_unit_id is not None:
        statement = statement.where(Decision.business_unit_id == business_unit_id)
    if status:
        statement = statement.where(Decision.status == status)
    
    # 新着順でソート
    statement = statement.order_by(Decision.created_at.desc()).offset(skip).limit(limit)
    
    decisions = session.exec(statement).all()
    
    result = []
    for decision in decisions:
        business_unit = None
        if decision.business_unit_id:
            business_unit = session.get(BusinessUnit, decision.business_unit_id)
        
        created_by = session.get(User, decision.created_by_user_id)
        
        result.append(DecisionResponse(
            id=decision.id,
            tenant_id=decision.tenant_id,
            business_unit_id=decision.business_unit_id,
            business_unit_name=business_unit.name if business_unit else None,
            title=decision.title,
            content=decision.content,
            status=decision.status.value,
            created_by_user_id=decision.created_by_user_id,
            created_by_name=created_by.full_name if created_by else None,
            created_at=decision.created_at.isoformat() if decision.created_at else "",
            updated_at=decision.updated_at.isoformat() if decision.updated_at else ""
        ))
    
    return result


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    decision_data: DecisionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    Decisionを作成

    権限: head/admin のみ
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
    
    # 事業部門の確認
    business_unit_id = decision_data.business_unit_id
    if business_unit_id:
        business_unit = session.get(BusinessUnit, business_unit_id)
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事業部門が見つかりません"
            )
    
    # Decisionを作成
    decision = Decision(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        title=decision_data.title,
        content=decision_data.content,
        status=DecisionStatus.PLANNED,
        created_by_user_id=current_user.id
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    
    # 関連Insightとの紐づけ（将来的に中間テーブルで実装）
    # 今回は一旦スキップ
    
    # レスポンスを構築
    business_unit = None
    if decision.business_unit_id:
        business_unit = session.get(BusinessUnit, decision.business_unit_id)
    created_by = session.get(User, decision.created_by_user_id)
    
    return DecisionResponse(
        id=decision.id,
        tenant_id=decision.tenant_id,
        business_unit_id=decision.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=decision.title,
        content=decision.content,
        status=decision.status.value,
        created_by_user_id=decision.created_by_user_id,
        created_by_name=created_by.full_name if created_by else None,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
        updated_at=decision.updated_at.isoformat() if decision.updated_at else ""
    )


@router.patch("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: int,
    decision_data: DecisionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    Decisionを更新

    権限: head/admin のみ
    """
    decision = session.get(Decision, decision_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decisionが見つかりません"
        )
    
    # 更新
    update_data = decision_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(decision, key, value)
    
    decision.updated_at = datetime.utcnow()
    session.add(decision)
    session.commit()
    session.refresh(decision)
    
    # レスポンスを構築
    business_unit = None
    if decision.business_unit_id:
        business_unit = session.get(BusinessUnit, decision.business_unit_id)
    created_by = session.get(User, decision.created_by_user_id)
    
    return DecisionResponse(
        id=decision.id,
        tenant_id=decision.tenant_id,
        business_unit_id=decision.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=decision.title,
        content=decision.content,
        status=decision.status.value,
        created_by_user_id=decision.created_by_user_id,
        created_by_name=created_by.full_name if created_by else None,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
        updated_at=decision.updated_at.isoformat() if decision.updated_at else ""
    )


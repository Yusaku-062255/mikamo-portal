"""
Insight API

AIによる分析・提案を管理するAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.models.insight import Insight, InsightType
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user, require_role
from datetime import datetime

router = APIRouter()


class InsightCreate(BaseModel):
    """Insight作成リクエスト"""
    title: str
    content: str
    type: InsightType
    score: int = Field(default=0, ge=0, le=100)
    business_unit_id: Optional[int] = None


class InsightUpdate(BaseModel):
    """Insight更新リクエスト"""
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[InsightType] = None
    score: Optional[int] = Field(None, ge=0, le=100)


class InsightResponse(BaseModel):
    """Insightレスポンス"""
    id: int
    tenant_id: int
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    title: str
    content: str
    type: str
    score: int
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Fieldをインポート
from pydantic import Field


@router.get("", response_model=List[InsightResponse])
async def list_insights(
    business_unit_id: Optional[int] = Query(None, description="事業部門IDで絞り込み"),
    type: Optional[InsightType] = Query(None, description="タイプで絞り込み"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="最小スコア"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Insight一覧を取得（スコアの高い順）
    
    権限:
    - staff/manager: 自分の事業部門 + 全社共通のInsightのみ閲覧可能
    - head/admin: 全部門のInsightを閲覧可能
    """
    statement = select(Insight)
    
    # テナントで絞り込み
    if current_user.tenant_id:
        statement = statement.where(Insight.tenant_id == current_user.tenant_id)
    
    # ロールに応じた権限チェック
    if current_user.role in ["staff", "manager"]:
        # 自分の事業部門 + 全社共通
        if current_user.business_unit_id:
            from sqlmodel import or_
            statement = statement.where(
                or_(
                    Insight.business_unit_id == current_user.business_unit_id,
                    Insight.business_unit_id.is_(None)
                )
            )
        else:
            statement = statement.where(Insight.business_unit_id.is_(None))
    
    # フィルター
    if business_unit_id is not None:
        statement = statement.where(Insight.business_unit_id == business_unit_id)
    if type:
        statement = statement.where(Insight.type == type)
    if min_score is not None:
        statement = statement.where(Insight.score >= min_score)
    
    # スコアの高い順でソート
    statement = statement.order_by(Insight.score.desc(), Insight.created_at.desc()).offset(skip).limit(limit)
    
    insights = session.exec(statement).all()
    
    result = []
    for insight in insights:
        business_unit = None
        if insight.business_unit_id:
            business_unit = session.get(BusinessUnit, insight.business_unit_id)
        
        created_by = None
        if insight.created_by:
            created_by = session.get(User, insight.created_by)
        
        result.append(InsightResponse(
            id=insight.id,
            tenant_id=insight.tenant_id,
            business_unit_id=insight.business_unit_id,
            business_unit_name=business_unit.name if business_unit else None,
            title=insight.title,
            content=insight.content,
            type=insight.type.value,
            score=insight.score,
            created_by=insight.created_by,
            created_by_name=created_by.full_name if created_by else None,
            created_at=insight.created_at.isoformat() if insight.created_at else "",
            updated_at=insight.updated_at.isoformat() if insight.updated_at else ""
        ))
    
    return result


@router.post("", response_model=InsightResponse, status_code=status.HTTP_201_CREATED)
async def create_insight(
    insight_data: InsightCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Insightを作成
    
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
    business_unit_id = insight_data.business_unit_id
    if business_unit_id:
        business_unit = session.get(BusinessUnit, business_unit_id)
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事業部門が見つかりません"
            )
    
    # Insightを作成
    insight = Insight(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        title=insight_data.title,
        content=insight_data.content,
        type=insight_data.type,
        score=insight_data.score,
        created_by=current_user.id
    )
    session.add(insight)
    session.commit()
    session.refresh(insight)
    
    # レスポンスを構築
    business_unit = None
    if insight.business_unit_id:
        business_unit = session.get(BusinessUnit, insight.business_unit_id)
    created_by = None
    if insight.created_by:
        created_by = session.get(User, insight.created_by)
    
    return InsightResponse(
        id=insight.id,
        tenant_id=insight.tenant_id,
        business_unit_id=insight.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=insight.title,
        content=insight.content,
        type=insight.type.value,
        score=insight.score,
        created_by=insight.created_by,
        created_by_name=created_by.full_name if created_by else None,
        created_at=insight.created_at.isoformat() if insight.created_at else "",
        updated_at=insight.updated_at.isoformat() if insight.updated_at else ""
    )


@router.patch("/{insight_id}", response_model=InsightResponse)
async def update_insight(
    insight_id: int,
    insight_data: InsightUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: None = Depends(require_role("head", "admin"))
):
    """
    Insightを更新
    
    権限: head/admin のみ
    """
    insight = session.get(Insight, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insightが見つかりません"
        )
    
    # 更新
    update_data = insight_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(insight, key, value)
    
    insight.updated_at = datetime.utcnow()
    session.add(insight)
    session.commit()
    session.refresh(insight)
    
    # レスポンスを構築
    business_unit = None
    if insight.business_unit_id:
        business_unit = session.get(BusinessUnit, insight.business_unit_id)
    created_by = None
    if insight.created_by:
        created_by = session.get(User, insight.created_by)
    
    return InsightResponse(
        id=insight.id,
        tenant_id=insight.tenant_id,
        business_unit_id=insight.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=insight.title,
        content=insight.content,
        type=insight.type.value,
        score=insight.score,
        created_by=insight.created_by,
        created_by_name=created_by.full_name if created_by else None,
        created_at=insight.created_at.isoformat() if insight.created_at else "",
        updated_at=insight.updated_at.isoformat() if insight.updated_at else ""
    )


"""
Issue API

現場での"困りごと"・トピックを管理するAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, or_
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.models.issue import Issue, IssueStatus, IssueTopic
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user, require_role
from datetime import datetime

router = APIRouter()


class IssueCreate(BaseModel):
    """Issue作成リクエスト"""
    title: str
    description: str
    topic: IssueTopic = IssueTopic.OTHER
    business_unit_id: Optional[int] = None
    conversation_id: Optional[int] = None


class IssueUpdate(BaseModel):
    """Issue更新リクエスト"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    topic: Optional[IssueTopic] = None


class IssueResponse(BaseModel):
    """Issueレスポンス"""
    id: int
    tenant_id: int
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    title: str
    description: str
    status: str
    topic: str
    created_by_user_id: int
    created_by_name: Optional[str] = None
    conversation_id: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[IssueResponse])
async def list_issues(
    business_unit_id: Optional[int] = Query(None, description="事業部門IDで絞り込み"),
    status: Optional[IssueStatus] = Query(None, description="ステータスで絞り込み"),
    topic: Optional[IssueTopic] = Query(None, description="トピックで絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Issue一覧を取得
    
    権限:
    - staff/manager: 自分の事業部門のIssueのみ閲覧可能
    - head/admin: 全部門のIssueを閲覧可能
    """
    statement = select(Issue)
    
    # テナントで絞り込み
    if current_user.tenant_id:
        statement = statement.where(Issue.tenant_id == current_user.tenant_id)
    
    # ロールに応じた権限チェック
    if current_user.role in ["staff", "manager"]:
        # 自分の事業部門のみ
        if current_user.business_unit_id:
            statement = statement.where(Issue.business_unit_id == current_user.business_unit_id)
        else:
            return []
    
    # フィルター
    if business_unit_id:
        statement = statement.where(Issue.business_unit_id == business_unit_id)
    if status:
        statement = statement.where(Issue.status == status)
    if topic:
        statement = statement.where(Issue.topic == topic)
    
    # 新着順でソート
    statement = statement.order_by(Issue.created_at.desc()).offset(skip).limit(limit)
    
    issues = session.exec(statement).all()
    
    result = []
    for issue in issues:
        business_unit = None
        if issue.business_unit_id:
            business_unit = session.get(BusinessUnit, issue.business_unit_id)
        
        created_by = session.get(User, issue.created_by_user_id)
        
        result.append(IssueResponse(
            id=issue.id,
            tenant_id=issue.tenant_id,
            business_unit_id=issue.business_unit_id,
            business_unit_name=business_unit.name if business_unit else None,
            title=issue.title,
            description=issue.description,
            status=issue.status.value,
            topic=issue.topic.value,
            created_by_user_id=issue.created_by_user_id,
            created_by_name=created_by.full_name if created_by else None,
            conversation_id=issue.conversation_id,
            created_at=issue.created_at.isoformat() if issue.created_at else "",
            updated_at=issue.updated_at.isoformat() if issue.updated_at else ""
        ))
    
    return result


@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Issueを作成
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
    business_unit_id = issue_data.business_unit_id
    if not business_unit_id:
        business_unit_id = current_user.business_unit_id
    
    if business_unit_id:
        business_unit = session.get(BusinessUnit, business_unit_id)
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事業部門が見つかりません"
            )
    
    # Issueを作成
    issue = Issue(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        title=issue_data.title,
        description=issue_data.description,
        status=IssueStatus.OPEN,
        topic=issue_data.topic,
        created_by_user_id=current_user.id,
        conversation_id=issue_data.conversation_id
    )
    session.add(issue)
    session.commit()
    session.refresh(issue)
    
    # レスポンスを構築
    business_unit = None
    if issue.business_unit_id:
        business_unit = session.get(BusinessUnit, issue.business_unit_id)
    created_by = session.get(User, issue.created_by_user_id)
    
    return IssueResponse(
        id=issue.id,
        tenant_id=issue.tenant_id,
        business_unit_id=issue.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=issue.title,
        description=issue.description,
        status=issue.status.value,
        topic=issue.topic.value,
        created_by_user_id=issue.created_by_user_id,
        created_by_name=created_by.full_name if created_by else None,
        conversation_id=issue.conversation_id,
        created_at=issue.created_at.isoformat() if issue.created_at else "",
        updated_at=issue.updated_at.isoformat() if issue.updated_at else ""
    )


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Issueを取得
    """
    issue = session.get(Issue, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issueが見つかりません"
        )
    
    # 権限チェック
    if current_user.role in ["staff", "manager"]:
        if issue.business_unit_id != current_user.business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このIssueを閲覧する権限がありません"
            )
    
    business_unit = None
    if issue.business_unit_id:
        business_unit = session.get(BusinessUnit, issue.business_unit_id)
    created_by = session.get(User, issue.created_by_user_id)
    
    return IssueResponse(
        id=issue.id,
        tenant_id=issue.tenant_id,
        business_unit_id=issue.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=issue.title,
        description=issue.description,
        status=issue.status.value,
        topic=issue.topic.value,
        created_by_user_id=issue.created_by_user_id,
        created_by_name=created_by.full_name if created_by else None,
        conversation_id=issue.conversation_id,
        created_at=issue.created_at.isoformat() if issue.created_at else "",
        updated_at=issue.updated_at.isoformat() if issue.updated_at else ""
    )


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    issue_data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Issueを更新
    
    権限:
    - 作成者またはmanager/head/adminのみ更新可能
    """
    issue = session.get(Issue, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issueが見つかりません"
        )
    
    # 権限チェック
    if issue.created_by_user_id != current_user.id and current_user.role not in ["manager", "head", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このIssueを更新する権限がありません"
        )
    
    # 更新
    update_data = issue_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(issue, key, value)
    
    issue.updated_at = datetime.utcnow()
    session.add(issue)
    session.commit()
    session.refresh(issue)
    
    # レスポンスを構築
    business_unit = None
    if issue.business_unit_id:
        business_unit = session.get(BusinessUnit, issue.business_unit_id)
    created_by = session.get(User, issue.created_by_user_id)
    
    return IssueResponse(
        id=issue.id,
        tenant_id=issue.tenant_id,
        business_unit_id=issue.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=issue.title,
        description=issue.description,
        status=issue.status.value,
        topic=issue.topic.value,
        created_by_user_id=issue.created_by_user_id,
        created_by_name=created_by.full_name if created_by else None,
        conversation_id=issue.conversation_id,
        created_at=issue.created_at.isoformat() if issue.created_at else "",
        updated_at=issue.updated_at.isoformat() if issue.updated_at else ""
    )


"""
ナレッジベースAPI

ミカモグループの社内情報（レシピ、オペレーションメモ、キャンペーン振り返り、マニュアル、経営方針など）
を管理するAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, or_
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.models.knowledge_item import KnowledgeItem
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user, require_role
from datetime import datetime

router = APIRouter()


# リクエスト/レスポンスモデル
class KnowledgeItemCreate(BaseModel):
    """ナレッジアイテム作成リクエスト"""
    title: str
    content: str
    business_unit_id: Optional[int] = None  # Noneの場合は全社共通
    category: Optional[str] = None  # カテゴリ（例：DXレポート、レシピ、マニュアル）
    source: Optional[str] = None  # 情報元（例：Claude調査、社内資料）
    tags: Optional[List[str]] = None


class KnowledgeItemUpdate(BaseModel):
    """ナレッジアイテム更新リクエスト"""
    title: Optional[str] = None
    content: Optional[str] = None
    business_unit_id: Optional[int] = None
    category: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None


class KnowledgeItemResponse(BaseModel):
    """ナレッジアイテムレスポンス"""
    id: int
    tenant_id: int
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    title: str
    content: str
    category: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: int
    created_by_name: Optional[str] = None
    updated_by: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[KnowledgeItemResponse])
async def list_knowledge_items(
    q: Optional[str] = Query(None, description="検索クエリ（タイトル・本文から検索）"),
    business_unit_id: Optional[int] = Query(None, description="事業部門IDで絞り込み"),
    tag: Optional[str] = Query(None, description="タグで絞り込み"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    ナレッジアイテム一覧を取得
    
    検索条件:
    - q: 全文検索（タイトル・本文）
    - business_unit_id: 事業部門ID
    - tag: タグ
    
    権限:
    - 自分のテナントのナレッジのみ閲覧可能
    - staff/manager: 自分の事業部門 + 全社共通（business_unit_id=None）
    - head/admin: 全部門のナレッジを閲覧可能
    """
    # テナントで絞り込み（将来のマルチテナント対応）
    statement = select(KnowledgeItem)
    
    if current_user.tenant_id:
        statement = statement.where(KnowledgeItem.tenant_id == current_user.tenant_id)
    
    # ロールに応じた権限チェック
    if current_user.role in ["staff", "manager"]:
        # 自分の事業部門 + 全社共通
        if current_user.business_unit_id:
            statement = statement.where(
                or_(
                    KnowledgeItem.business_unit_id == current_user.business_unit_id,
                    KnowledgeItem.business_unit_id.is_(None)
                )
            )
    
    # 検索条件
    if q:
        # シンプルな全文検索（将来的にベクトル検索に拡張可能）
        statement = statement.where(
            or_(
                KnowledgeItem.title.contains(q),
                KnowledgeItem.content.contains(q)
            )
        )
    
    if business_unit_id is not None:
        statement = statement.where(KnowledgeItem.business_unit_id == business_unit_id)
    
    if tag:
        # PostgreSQLの配列検索（tags配列にtagが含まれる）
        # 注意: SQLModel/SQLAlchemyでの配列検索は実装が複雑なため、
        # ここでは簡易的にcontentに含まれるかで検索（将来的に改善）
        statement = statement.where(KnowledgeItem.content.contains(tag))
    
    items = session.exec(statement.order_by(KnowledgeItem.updated_at.desc())).all()
    
    # レスポンスに事業部門名と作成者名を追加
    result = []
    for item in items:
        business_unit = None
        if item.business_unit_id:
            business_unit = session.get(BusinessUnit, item.business_unit_id)
        
        creator = session.get(User, item.created_by)
        
        result.append(KnowledgeItemResponse(
            id=item.id,
            tenant_id=item.tenant_id,
            business_unit_id=item.business_unit_id,
            business_unit_name=business_unit.name if business_unit else None,
            title=item.title,
            content=item.content,
            category=item.category,
            source=item.source,
            tags=item.tags,
            created_by=item.created_by,
            created_by_name=creator.full_name if creator else None,
            updated_by=item.updated_by,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else ""
        ))

    return result


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(
    item_data: KnowledgeItemCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    ナレッジアイテムを作成
    
    権限:
    - 全ロールが作成可能（自分のテナント内）
    """
    # テナントIDを取得（ユーザーのテナントIDを使用）
    tenant_id = current_user.tenant_id
    if not tenant_id:
        # テナントIDが未設定の場合はデフォルトでmikamoテナントを取得
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
    
    # 事業部門の存在確認
    if item_data.business_unit_id:
        business_unit = session.get(BusinessUnit, item_data.business_unit_id)
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された事業部門が見つかりません"
            )
    
    # ナレッジアイテムを作成
    knowledge_item = KnowledgeItem(
        tenant_id=tenant_id,
        business_unit_id=item_data.business_unit_id,
        title=item_data.title,
        content=item_data.content,
        category=item_data.category,
        source=item_data.source,
        tags=item_data.tags or [],
        created_by=current_user.id
    )
    session.add(knowledge_item)
    session.commit()
    session.refresh(knowledge_item)
    
    # レスポンスを構築
    business_unit = None
    if knowledge_item.business_unit_id:
        business_unit = session.get(BusinessUnit, knowledge_item.business_unit_id)
    
    creator = session.get(User, knowledge_item.created_by)
    
    return KnowledgeItemResponse(
        id=knowledge_item.id,
        tenant_id=knowledge_item.tenant_id,
        business_unit_id=knowledge_item.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=knowledge_item.title,
        content=knowledge_item.content,
        category=knowledge_item.category,
        source=knowledge_item.source,
        tags=knowledge_item.tags,
        created_by=knowledge_item.created_by,
        created_by_name=creator.full_name if creator else None,
        updated_by=knowledge_item.updated_by,
        created_at=knowledge_item.created_at.isoformat() if knowledge_item.created_at else "",
        updated_at=knowledge_item.updated_at.isoformat() if knowledge_item.updated_at else ""
    )


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    ナレッジアイテムを取得
    
    権限:
    - 自分のテナントのナレッジのみ閲覧可能
    - staff/manager: 自分の事業部門 + 全社共通
    - head/admin: 全部門のナレッジを閲覧可能
    """
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ナレッジアイテムが見つかりません"
        )
    
    # テナントチェック
    if current_user.tenant_id and item.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このナレッジアイテムにアクセスする権限がありません"
        )
    
    # ロールに応じた権限チェック
    if current_user.role in ["staff", "manager"]:
        if item.business_unit_id and item.business_unit_id != current_user.business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このナレッジアイテムにアクセスする権限がありません"
            )
    
    # レスポンスを構築
    business_unit = None
    if item.business_unit_id:
        business_unit = session.get(BusinessUnit, item.business_unit_id)
    
    creator = session.get(User, item.created_by)
    updater = None
    if item.updated_by:
        updater = session.get(User, item.updated_by)
    
    return KnowledgeItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        business_unit_id=item.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=item.title,
        content=item.content,
        category=item.category,
        source=item.source,
        tags=item.tags,
        created_by=item.created_by,
        created_by_name=creator.full_name if creator else None,
        updated_by=item.updated_by,
        created_at=item.created_at.isoformat() if item.created_at else "",
        updated_at=item.updated_at.isoformat() if item.updated_at else ""
    )


@router.put("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge_item(
    item_id: int,
    item_data: KnowledgeItemUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    ナレッジアイテムを更新
    
    権限:
    - 作成者のみ更新可能（またはadmin/head）
    """
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ナレッジアイテムが見つかりません"
        )
    
    # 権限チェック（作成者またはadmin/head）
    if item.created_by != current_user.id and current_user.role not in ["admin", "head"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このナレッジアイテムを更新する権限がありません"
        )
    
    # 更新
    if item_data.title is not None:
        item.title = item_data.title
    if item_data.content is not None:
        item.content = item_data.content
    if item_data.business_unit_id is not None:
        # 事業部門の存在確認
        if item_data.business_unit_id:
            business_unit = session.get(BusinessUnit, item_data.business_unit_id)
            if not business_unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定された事業部門が見つかりません"
                )
        item.business_unit_id = item_data.business_unit_id
    if item_data.category is not None:
        item.category = item_data.category
    if item_data.source is not None:
        item.source = item_data.source
    if item_data.tags is not None:
        item.tags = item_data.tags
    
    item.updated_by = current_user.id
    item.updated_at = datetime.utcnow()
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # レスポンスを構築
    business_unit = None
    if item.business_unit_id:
        business_unit = session.get(BusinessUnit, item.business_unit_id)
    
    creator = session.get(User, item.created_by)
    updater = session.get(User, item.updated_by) if item.updated_by else None
    
    return KnowledgeItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        business_unit_id=item.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        title=item.title,
        content=item.content,
        category=item.category,
        source=item.source,
        tags=item.tags,
        created_by=item.created_by,
        created_by_name=creator.full_name if creator else None,
        updated_by=item.updated_by,
        created_at=item.created_at.isoformat() if item.created_at else "",
        updated_at=item.updated_at.isoformat() if item.updated_at else ""
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_item(
    item_id: int,
    current_user: User = Depends(require_role("admin", "head")()),
    session: Session = Depends(get_session)
):
    """
    ナレッジアイテムを削除
    
    権限:
    - admin/headのみ削除可能
    """
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ナレッジアイテムが見つかりません"
        )
    
    session.delete(item)
    session.commit()
    return None


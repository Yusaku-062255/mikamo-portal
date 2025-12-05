"""
ナレッジベースリポジトリ

ナレッジアイテムの検索・取得ロジック
将来的にベクトル検索（RAG）に対応できる設計
"""
from sqlmodel import Session, select, or_
from sqlalchemy import func
from typing import List, Optional
from app.models.knowledge_item import KnowledgeItem
from app.models.business_unit import BusinessUnit


def search_knowledge_items(
    session: Session,
    query: str,
    business_unit_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 5
) -> List[KnowledgeItem]:
    """
    ナレッジアイテムを検索（全文検索）

    Args:
        session: データベースセッション
        query: 検索クエリ
        business_unit_id: 事業部門ID（Noneの場合は全社共通も含む）
        tenant_id: テナントID（マルチテナント対応）
        category: カテゴリ（例: "menu", "manual"）
        tags: タグリスト（例: ["cafe", "lunch"]）- すべてのタグを含むものを検索
        limit: 取得件数

    Returns:
        ナレッジアイテムリスト
    """
    statement = select(KnowledgeItem).where(KnowledgeItem.is_active == True)

    # テナントで絞り込み
    if tenant_id is not None:
        statement = statement.where(KnowledgeItem.tenant_id == tenant_id)

    # 検索クエリで絞り込み（タイトル・本文）
    if query:
        statement = statement.where(
            or_(
                KnowledgeItem.title.contains(query),
                KnowledgeItem.content.contains(query)
            )
        )

    # 事業部門で絞り込み
    if business_unit_id is not None:
        statement = statement.where(
            or_(
                KnowledgeItem.business_unit_id == business_unit_id,
                KnowledgeItem.business_unit_id.is_(None)  # 全社共通も含む
            )
        )

    # カテゴリで絞り込み
    if category is not None:
        statement = statement.where(KnowledgeItem.category == category)

    # タグで絞り込み（PostgreSQL ARRAYの @> 演算子を使用）
    if tags:
        statement = statement.where(KnowledgeItem.tags.contains(tags))

    items = session.exec(
        statement.order_by(KnowledgeItem.updated_at.desc()).limit(limit)
    ).all()

    return items


def search_menu_items(
    session: Session,
    business_unit_id: Optional[int] = None,
    tenant_id: int = 1,
    menu_group: Optional[str] = None,
    limit: int = 10
) -> List[KnowledgeItem]:
    """
    メニューアイテムを検索（カフェメニュー等）

    Args:
        session: データベースセッション
        business_unit_id: 事業部門ID
        tenant_id: テナントID
        menu_group: メニューグループ（例: "lunch", "dessert"）
        limit: 取得件数

    Returns:
        メニューナレッジアイテムリスト
    """
    tags = ["menu"]
    if menu_group:
        tags.append(menu_group)

    return search_knowledge_items(
        session=session,
        query="",
        business_unit_id=business_unit_id,
        tenant_id=tenant_id,
        category="menu",
        tags=tags,
        limit=limit
    )


def get_knowledge_context(
    session: Session,
    query: str,
    business_unit_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 3,
    include_full_content: bool = False
) -> str:
    """
    ナレッジアイテムからコンテキスト文字列を生成

    Args:
        session: データベースセッション
        query: 検索クエリ
        business_unit_id: 事業部門ID
        tenant_id: テナントID
        category: カテゴリ
        tags: タグリスト
        limit: 取得件数
        include_full_content: 本文全体を含めるかどうか

    Returns:
        コンテキスト文字列（Markdown形式）
    """
    items = search_knowledge_items(
        session=session,
        query=query,
        business_unit_id=business_unit_id,
        tenant_id=tenant_id,
        category=category,
        tags=tags,
        limit=limit
    )

    if not items:
        return ""

    context_parts = ["【関連ナレッジ情報】"]
    for item in items:
        context_parts.append(f"\n## {item.title}")
        # 本文の取得（include_full_contentがTrueの場合は全文、Falseの場合は最初の200文字）
        if include_full_content:
            context_parts.append(item.content)
        else:
            content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
            context_parts.append(content_preview)
        if item.tags:
            context_parts.append(f"\nタグ: {', '.join(item.tags)}")

    return "\n".join(context_parts)


def get_menu_context(
    session: Session,
    business_unit_id: Optional[int] = None,
    tenant_id: int = 1,
    menu_group: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    メニュー情報からコンテキスト文字列を生成（AI用）

    Args:
        session: データベースセッション
        business_unit_id: 事業部門ID
        tenant_id: テナントID
        menu_group: メニューグループ（例: "lunch", "dessert"）
        limit: 取得件数

    Returns:
        メニューコンテキスト文字列
    """
    tags = ["menu"]
    if menu_group:
        tags.append(menu_group)

    return get_knowledge_context(
        session=session,
        query="",
        business_unit_id=business_unit_id,
        tenant_id=tenant_id,
        category="menu",
        tags=tags,
        limit=limit,
        include_full_content=True  # メニューは全文を含める
    )


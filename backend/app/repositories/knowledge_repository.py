"""
ナレッジベースリポジトリ

ナレッジアイテムの検索・取得ロジック
将来的にベクトル検索（RAG）に対応できる設計
"""
from sqlmodel import Session, select, or_
from typing import List, Optional
from app.models.knowledge_item import KnowledgeItem
from app.models.business_unit import BusinessUnit


def search_knowledge_items(
    session: Session,
    query: str,
    business_unit_id: Optional[int] = None,
    limit: int = 5
) -> List[KnowledgeItem]:
    """
    ナレッジアイテムを検索（全文検索）
    
    Args:
        session: データベースセッション
        query: 検索クエリ
        business_unit_id: 事業部門ID（Noneの場合は全社共通も含む）
        limit: 取得件数
    
    Returns:
        ナレッジアイテムリスト
    """
    statement = select(KnowledgeItem)
    
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
    
    items = session.exec(
        statement.order_by(KnowledgeItem.updated_at.desc()).limit(limit)
    ).all()
    
    return items


def get_knowledge_context(
    session: Session,
    query: str,
    business_unit_id: Optional[int] = None,
    limit: int = 3
) -> str:
    """
    ナレッジアイテムからコンテキスト文字列を生成
    
    Args:
        session: データベースセッション
        query: 検索クエリ
        business_unit_id: 事業部門ID
        limit: 取得件数
    
    Returns:
        コンテキスト文字列（Markdown形式）
    """
    items = search_knowledge_items(session, query, business_unit_id, limit)
    
    if not items:
        return ""
    
    context_parts = ["【関連ナレッジ情報】"]
    for item in items:
        context_parts.append(f"\n## {item.title}")
        # 本文の最初の200文字を取得
        content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
        context_parts.append(content_preview)
        if item.tags:
            context_parts.append(f"\nタグ: {', '.join(item.tags)}")
    
    return "\n".join(context_parts)


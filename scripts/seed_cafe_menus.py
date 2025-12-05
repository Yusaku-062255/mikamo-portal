#!/usr/bin/env python3
"""
Cafe Menu Snapshot Seed Script

カフェのInstagramストーリーから取得したメニュー情報をKnowledgeItemとして保存する。
snapshot_keyをtitleに使用し、既存データがあればupdateする（upsert）。

Usage:
    python scripts/seed_cafe_menus.py
    python scripts/seed_cafe_menus.py --dry-run  # DBなしでプレビュー

Environment:
    DATABASE_URL must be set (or use default for local development)
"""

import sys
import os
from typing import Optional

# パスを追加してbackendモジュールをインポート可能にする
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# =============================================================================
# カフェメニュー定義（JSONスナップショット）
# =============================================================================

CAFE_MENUS = [
    {
        "snapshot_key": "cafe_menu_lunch_regular",
        "snapshot_date": "2025-03-11",
        "menu_group": "lunch_regular",
        "display_name": "ランチメニュー（レギュラー）",
        "items": [
            {"name": "コーヒーカレー", "price": 850, "note": "自家焙煎コーヒー入りの特製カレー"},
            {"name": "ナシゴレン", "price": 900, "note": "インドネシア風チャーハン"},
            {"name": "トムヤム麺", "price": 900, "note": "ピリ辛スープ麺"},
            {"name": "ガパオライス", "price": 900, "note": "タイ風バジル炒めご飯"},
            {"name": "タコライス", "price": 900, "note": "沖縄風タコミート丼"},
        ],
        "tags": ["menu", "cafe", "lunch", "regular"]
    },
    {
        "snapshot_key": "cafe_menu_softcream",
        "snapshot_date": "2025-03-11",
        "menu_group": "softcream",
        "display_name": "ソフトクリームメニュー",
        "items": [
            {"name": "バニラ", "price": 350, "note": None},
            {"name": "コーヒー", "price": 350, "note": "自家焙煎"},
            {"name": "ミックス", "price": 350, "note": "バニラ＋コーヒー"},
            {"name": "アフォガート", "price": 500, "note": "エスプレッソがけ"},
        ],
        "tags": ["menu", "cafe", "dessert", "softcream"]
    },
    {
        "snapshot_key": "cafe_menu_pancake",
        "snapshot_date": "2025-03-11",
        "menu_group": "pancake",
        "display_name": "パンケーキメニュー",
        "items": [
            {"name": "プレーンパンケーキ", "price": 700, "note": "バター＆メープル"},
            {"name": "チョコバナナパンケーキ", "price": 850, "note": ""},
            {"name": "季節のフルーツパンケーキ", "price": 950, "note": "いちご／マンゴー等"},
        ],
        "tags": ["menu", "cafe", "dessert", "pancake"]
    },
    {
        "snapshot_key": "cafe_menu_seasonal_vege",
        "snapshot_date": "2025-03-11",
        "menu_group": "seasonal_vegetables",
        "display_name": "旬野菜メニュー",
        "items": [
            {"name": "季節野菜のスープセット", "price": 650, "note": "日替わり"},
            {"name": "農家直送サラダプレート", "price": 800, "note": "ドレッシング選択可"},
        ],
        "tags": ["menu", "cafe", "lunch", "seasonal", "vegetables"]
    },
    {
        "snapshot_key": "cafe_menu_lunch_alt",
        "snapshot_date": "2025-03-20",
        "menu_group": "lunch_regular",
        "display_name": "ランチメニュー（レギュラー）更新版",
        "items": [
            {"name": "コーヒーカレー", "price": 850, "note": ""},
            {"name": "キーマカレー", "price": 900, "note": "新メニュー"},
            {"name": "トムヤム麺", "price": 900, "note": ""},
            {"name": "ガパオライス", "price": 900, "note": ""},
            {"name": "オムライス", "price": 950, "note": "デミグラス or ケチャップ"},
        ],
        "tags": ["menu", "cafe", "lunch", "regular", "updated"]
    },
]


def format_menu_content(menu_data: dict) -> str:
    """
    メニューデータをMarkdown形式でフォーマットする。
    AIが読みやすい形式で保存する。
    """
    lines = [
        f"# {menu_data['display_name']}",
        f"",
        f"**スナップショット日**: {menu_data['snapshot_date']}",
        f"**メニューグループ**: {menu_data['menu_group']}",
        f"",
        "## メニュー一覧",
        "",
    ]

    for item in menu_data["items"]:
        price_str = f"¥{item['price']:,}"
        note_str = f" - {item['note']}" if item.get('note') else ""
        lines.append(f"- **{item['name']}** ({price_str}){note_str}")

    lines.append("")
    lines.append(f"---")
    lines.append(f"_タグ: {', '.join(menu_data['tags'])}_")

    return "\n".join(lines)


def seed_cafe_menus(tenant_id: int = 1):
    """
    カフェメニューをシードする。
    """
    # ここでDBモジュールをインポート（遅延インポート）
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.knowledge_item import KnowledgeItem
    from app.models.business_unit import BusinessUnit
    from app.models.user import User

    print(f"\n=== カフェメニューシード開始 (tenant_id={tenant_id}) ===\n")

    with Session(engine) as session:
        # システムユーザーを取得
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.role == "admin"
        ).limit(1)
        admin_user = session.exec(stmt).first()

        if not admin_user:
            stmt = select(User).where(User.tenant_id == tenant_id).limit(1)
            admin_user = session.exec(stmt).first()

        if not admin_user:
            print(f"Error: テナント {tenant_id} にユーザーが存在しません。")
            return

        created_by = admin_user.id

        # カフェ事業部門を取得
        stmt = select(BusinessUnit).where(
            BusinessUnit.tenant_id == tenant_id,
            BusinessUnit.code == "cafe"
        )
        cafe_unit = session.exec(stmt).first()
        business_unit_id = cafe_unit.id if cafe_unit else None

        if not business_unit_id:
            print("Warning: カフェ事業部門（code='cafe'）が見つかりません。")

        print(f"Using user_id={created_by}, business_unit_id={business_unit_id}\n")

        # 各メニューをupsert
        for menu_data in CAFE_MENUS:
            title = menu_data["snapshot_key"]

            # 既存のKnowledgeItemを検索
            stmt = select(KnowledgeItem).where(
                KnowledgeItem.tenant_id == tenant_id,
                KnowledgeItem.title == title
            )
            existing = session.exec(stmt).first()

            content = format_menu_content(menu_data)
            tags = menu_data["tags"]

            if existing:
                # 更新
                existing.content = content
                existing.tags = tags
                existing.category = "menu"
                existing.source = f"instagram_story_{menu_data['snapshot_date']}"
                session.add(existing)
                print(f"  Updated: {title}")
            else:
                # 新規作成
                knowledge = KnowledgeItem(
                    tenant_id=tenant_id,
                    business_unit_id=business_unit_id,
                    title=title,
                    content=content,
                    category="menu",
                    source=f"instagram_story_{menu_data['snapshot_date']}",
                    tags=tags,
                    created_by=created_by,
                    is_active=True
                )
                session.add(knowledge)
                print(f"  Created: {title}")

        session.commit()
        print(f"\n=== シード完了: {len(CAFE_MENUS)}件のメニューを処理 ===\n")


def main():
    """
    メイン関数。
    コマンドライン引数でtenant_idを指定可能。
    """
    import argparse

    parser = argparse.ArgumentParser(description="カフェメニューシードスクリプト")
    parser.add_argument(
        "--tenant-id",
        type=int,
        default=1,
        help="テナントID（デフォルト: 1）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際にDBに保存せずに内容を表示"
    )

    args = parser.parse_args()

    if args.dry_run:
        print("=== Dry Run: メニュー内容プレビュー ===\n")
        for menu_data in CAFE_MENUS:
            print(f"--- {menu_data['snapshot_key']} ---")
            print(format_menu_content(menu_data))
            print()
        print(f"=== 合計: {len(CAFE_MENUS)}件のメニュー ===")
        return

    seed_cafe_menus(tenant_id=args.tenant_id)


if __name__ == "__main__":
    main()

"""
カラムマイグレーションヘルパー

SQLModel.metadata.create_all() は既存テーブルに新しいカラムを追加しないため、
このヘルパーで欠けているカラムを検出して追加する。
"""
from sqlalchemy import text, inspect
from app.core.database import engine


def add_missing_columns():
    """
    欠けているカラムをusersテーブルに追加する

    Cloud Runでの起動時に自動的に実行
    """
    with engine.connect() as conn:
        inspector = inspect(engine)

        # usersテーブルの既存カラムを取得
        try:
            columns = {col['name'] for col in inspector.get_columns('users')}
        except Exception as e:
            print(f"ℹ️  usersテーブルがまだ存在しません: {e}")
            return

        # tenant_id カラムを追加
        if 'tenant_id' not in columns:
            print("⏳ usersテーブルに tenant_id カラムを追加します...")
            try:
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
                """))
                conn.commit()
                print("✅ tenant_id カラムを追加しました")
            except Exception as e:
                print(f"⚠️  tenant_id カラムの追加でエラー: {e}")
        else:
            print("ℹ️  tenant_id カラムは既に存在します")

        # business_unit_id カラムを追加
        if 'business_unit_id' not in columns:
            print("⏳ usersテーブルに business_unit_id カラムを追加します...")
            try:
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS business_unit_id INTEGER REFERENCES business_units(id)
                """))
                conn.commit()
                print("✅ business_unit_id カラムを追加しました")
            except Exception as e:
                print(f"⚠️  business_unit_id カラムの追加でエラー: {e}")
        else:
            print("ℹ️  business_unit_id カラムは既に存在します")

        # knowledge_items テーブルのカラム
        try:
            ki_columns = {col['name'] for col in inspector.get_columns('knowledge_items')}

            if 'category' not in ki_columns:
                print("⏳ knowledge_itemsテーブルに category カラムを追加します...")
                try:
                    conn.execute(text("""
                        ALTER TABLE knowledge_items
                        ADD COLUMN IF NOT EXISTS category VARCHAR(255)
                    """))
                    conn.commit()
                    print("✅ category カラムを追加しました")
                except Exception as e:
                    print(f"⚠️  category カラムの追加でエラー: {e}")

            if 'source' not in ki_columns:
                print("⏳ knowledge_itemsテーブルに source カラムを追加します...")
                try:
                    conn.execute(text("""
                        ALTER TABLE knowledge_items
                        ADD COLUMN IF NOT EXISTS source VARCHAR(255)
                    """))
                    conn.commit()
                    print("✅ source カラムを追加しました")
                except Exception as e:
                    print(f"⚠️  source カラムの追加でエラー: {e}")
        except Exception as e:
            print(f"ℹ️  knowledge_itemsテーブルがまだ存在しません: {e}")


def run_migrations():
    """
    すべてのマイグレーションを実行
    """
    print("\n" + "=" * 60)
    print("🔄 データベースマイグレーション: 欠けているカラムを追加")
    print("=" * 60)
    add_missing_columns()
    print("=" * 60 + "\n")

"""
Database migration script for incremental schema updates.
Run this script after pulling backend schema changes into an existing database.

Usage: python migrate_db.py
"""

import asyncio
from sqlalchemy import text
from app.database import engine


async def migrate():
    """Apply additive schema changes required by newer backend versions.

    说明：该脚本面向“已有数据库”的增量升级，不替代init_database.py。
    """
    async with engine.begin() as conn:
        # Add new columns to users table
        print("Migrating users table...")
        user_columns = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS real_name VARCHAR(100)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",
        ]
        for sql in user_columns:
            try:
                await conn.execute(text(sql))
                print(f"  Executed: {sql[:50]}...")
            except Exception as e:
                print(f"  Skipped (may already exist): {str(e)[:50]}")

        # Add created_by columns to data tables
        print("\nMigrating market_data table...")
        await add_created_by_column(conn, "market_data")

        print("Migrating engineering_data table...")
        await add_created_by_column(conn, "engineering_data")

        print("Migrating finance_data table...")
        await add_created_by_column(conn, "finance_data")

        print("Migrating attachments table...")
        await ensure_attachment_module_schema(conn)

    print("\nMigration completed successfully!")


async def add_created_by_column(conn, table_name: str):
    """Add created_by column with foreign key to a table"""
    try:
        sql = f"""
        ALTER TABLE {table_name}
        ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE SET NULL
        """
        await conn.execute(text(sql))
        print(f"  Added created_by column to {table_name}")
    except Exception as e:
        print(f"  Skipped (may already exist): {str(e)[:50]}")


async def ensure_attachment_module_schema(conn):
    """Add attachmentmodule enum, module column, and supporting index for attachments.

    历史背景：附件模块化后，ORM模型新增Attachment.module；
    若旧库未升级会在项目删除/附件查询时触发“column attachments.module does not exist”。
    """
    statements = [
        """
        DO $$ BEGIN
            CREATE TYPE attachmentmodule AS ENUM ('PROJECT', 'MARKET', 'ENGINEERING', 'FINANCE');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$
        """,
        # 默认值需要显式cast到attachmentmodule，避免asyncpg对枚举文本解析失败。
        "ALTER TABLE attachments ADD COLUMN IF NOT EXISTS module attachmentmodule DEFAULT 'PROJECT'::attachmentmodule NOT NULL",
        "UPDATE attachments SET module = 'PROJECT'::attachmentmodule WHERE module IS NULL",
        "CREATE INDEX IF NOT EXISTS ix_attachments_module ON attachments(module)",
    ]

    for sql in statements:
        try:
            await conn.execute(text(sql))
            preview = " ".join(sql.split())[:70]
            print(f"  Executed: {preview}...")
        except Exception as e:
            print(f"  Skipped (may already exist): {str(e)[:80]}")


if __name__ == "__main__":
    asyncio.run(migrate())

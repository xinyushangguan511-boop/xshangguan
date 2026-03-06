"""
Database migration script to add new columns for user management feature.
Run this script once to update the database schema.

Usage: python migrate_db.py
"""

import asyncio
from sqlalchemy import text
from app.database import engine


async def migrate():
    """Add new columns to existing tables"""
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


if __name__ == "__main__":
    asyncio.run(migrate())

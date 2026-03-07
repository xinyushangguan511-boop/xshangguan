"""
Complete Database Initialization Script for MIS System

This script creates all database tables from scratch.
Run this when setting up the server for the first time.

Usage:
    python init_database.py                  # Create tables only
    python init_database.py --create-admin   # Create tables + admin user

Prerequisites:
    1. PostgreSQL installed and running
    2. Database created: CREATE DATABASE mis_db;
    3. .env file configured with DATABASE_URL
"""

import asyncio
import argparse
import getpass
import sys
from sqlalchemy import text


# ============================================================
# SQL Schema Definition
# ============================================================

SCHEMA_SQL = """
-- ============================================================
-- MIS Database Schema
-- Cross-Department Management Information System
-- ============================================================

-- Drop existing tables (optional, comment out to preserve data)
-- DROP TABLE IF EXISTS attachments CASCADE;
-- DROP TABLE IF EXISTS finance_data CASCADE;
-- DROP TABLE IF EXISTS engineering_data CASCADE;
-- DROP TABLE IF EXISTS market_data CASCADE;
-- DROP TABLE IF EXISTS projects CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- ENUM Types
-- ============================================================

DO $$ BEGIN
    CREATE TYPE department AS ENUM ('market', 'engineering', 'finance', 'admin');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE projectstatus AS ENUM ('planning', 'in_progress', 'completed', 'suspended');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- Users Table
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    department department NOT NULL,
    real_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_department ON users(department);

-- ============================================================
-- Projects Table
-- ============================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    construction_unit VARCHAR(200),
    location VARCHAR(200),
    contract_start_date DATE,
    contract_end_date DATE,
    contract_duration INTEGER,
    actual_start_date DATE,
    status projectstatus DEFAULT 'planning' NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_projects_project_code ON projects(project_code);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS ix_projects_created_by ON projects(created_by);

-- ============================================================
-- Market Data Table
-- ============================================================

CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    building_area DECIMAL(15, 2),
    structure VARCHAR(100),
    floors INTEGER,
    contract_value DECIMAL(15, 2),
    prepayment_ratio DECIMAL(5, 2),
    advance_amount DECIMAL(15, 2),
    progress_payment_ratio DECIMAL(5, 2),
    contract_type VARCHAR(100),
    remarks TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT uix_market_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_market_data_project_id ON market_data(project_id);
CREATE INDEX IF NOT EXISTS ix_market_data_year_month ON market_data(year, month);

-- ============================================================
-- Engineering Data Table
-- ============================================================

CREATE TABLE IF NOT EXISTS engineering_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    actual_duration INTEGER,
    end_period_progress VARCHAR(200),
    contract_value DECIMAL(15, 2),
    monthly_output DECIMAL(15, 2),
    planned_output DECIMAL(15, 2),
    monthly_approval DECIMAL(15, 2),
    staff_count INTEGER,
    next_month_plan DECIMAL(15, 2),
    remarks TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT uix_engineering_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_engineering_data_project_id ON engineering_data(project_id);
CREATE INDEX IF NOT EXISTS ix_engineering_data_year_month ON engineering_data(year, month);

-- ============================================================
-- Finance Data Table
-- ============================================================

CREATE TABLE IF NOT EXISTS finance_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    monthly_revenue DECIMAL(15, 2),
    monthly_cost DECIMAL(15, 2),
    monthly_payment_received DECIMAL(15, 2),
    target_margin DECIMAL(5, 2),
    remarks TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT uix_finance_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_finance_data_project_id ON finance_data(project_id);
CREATE INDEX IF NOT EXISTS ix_finance_data_year_month ON finance_data(year, month);

-- ============================================================
-- Attachments Table
-- ============================================================

CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    department department NOT NULL,
    file_type VARCHAR(50),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_attachments_project_id ON attachments(project_id);
CREATE INDEX IF NOT EXISTS ix_attachments_department ON attachments(department);
CREATE INDEX IF NOT EXISTS ix_attachments_uploaded_by ON attachments(uploaded_by);
"""


async def init_database(create_admin: bool = False):
    """Initialize the database with all tables"""

    # Import here to ensure .env is loaded
    from app.database import engine
    from app.utils.security import get_password_hash

    print("=" * 60)
    print("MIS Database Initialization")
    print("=" * 60)

    # Create tables
    print("\n[1/3] Creating database tables...")
    async with engine.begin() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in SCHEMA_SQL.split(';') if s.strip()]
        for i, stmt in enumerate(statements):
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                error_msg = str(e).lower()
                # Ignore "already exists" errors
                if 'already exists' not in error_msg and 'duplicate' not in error_msg:
                    print(f"  Warning: {str(e)[:100]}")

    print("  Tables created successfully!")

    # Verify tables
    print("\n[2/3] Verifying tables...")
    tables = ['users', 'projects', 'market_data', 'engineering_data', 'finance_data', 'attachments']
    async with engine.begin() as conn:
        for table in tables:
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"
            ), {"t": table})
            exists = result.scalar()
            status = "OK" if exists else "MISSING"
            print(f"  - {table}: {status}")

    # Create admin user
    print("\n[3/3] Admin user setup...")
    if create_admin:
        username = input("  Enter admin username: ").strip()
        if not username or len(username) < 3:
            print("  Error: Username must be at least 3 characters!")
            return False

        password = getpass.getpass("  Enter admin password: ")
        if len(password) < 6:
            print("  Error: Password must be at least 6 characters!")
            return False

        confirm = getpass.getpass("  Confirm password: ")
        if password != confirm:
            print("  Error: Passwords do not match!")
            return False

        # Check if user exists
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT id FROM users WHERE username = :u"
            ), {"u": username})
            if result.scalar_one_or_none():
                print(f"  Error: User '{username}' already exists!")
                return False

            # Create admin user
            password_hash = get_password_hash(password)
            await conn.execute(text("""
                INSERT INTO users (username, password_hash, department, is_active)
                VALUES (:username, :password_hash, 'admin', true)
            """), {"username": username, "password_hash": password_hash})

        print(f"  Admin user '{username}' created successfully!")
    else:
        print("  Skipped (use --create-admin to create admin user)")

    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start backend:  python -m uvicorn app.main:app --reload")
    print("  2. Start frontend: cd ../frontend && npm run dev")
    print("  3. Open browser:   http://localhost:5173")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Initialize MIS database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python init_database.py                  Create tables only
  python init_database.py --create-admin   Create tables + admin user

Prerequisites:
  1. PostgreSQL running with database created
  2. .env file configured with DATABASE_URL
        """
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create an initial admin user after table creation"
    )
    args = parser.parse_args()

    try:
        asyncio.run(init_database(create_admin=args.create_admin))
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists (CREATE DATABASE mis_db;)")
        print("  3. .env file has correct DATABASE_URL")
        sys.exit(1)


if __name__ == "__main__":
    main()

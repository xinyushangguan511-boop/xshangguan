"""
Complete Database Initialization Script for MIS System

This script creates all database tables from scratch.
Run this when setting up the server for the first time.

Usage:
    python init_database.py

Optional: Create initial admin user
    python init_database.py --create-admin
"""

import asyncio
import argparse
import getpass
from sqlalchemy import text
from app.database import engine, Base

# Import all models to register them with Base
from app.models.user import User, Department
from app.models.project import Project, ProjectStatus
from app.models.market import MarketData
from app.models.engineering import EngineeringData
from app.models.finance import FinanceData
from app.models.attachment import Attachment


# SQL statements for creating tables with all constraints
CREATE_TABLES_SQL = """
-- Create enum types
DO $$ BEGIN
    CREATE TYPE department AS ENUM ('market', 'engineering', 'finance', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE projectstatus AS ENUM ('planning', 'in_progress', 'completed', 'suspended');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    department department NOT NULL,
    real_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- Projects table
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
    status projectstatus DEFAULT 'planning',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_projects_project_code ON projects(project_code);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
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
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uix_market_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_market_data_project_id ON market_data(project_id);

-- Engineering data table
CREATE TABLE IF NOT EXISTS engineering_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
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
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uix_engineering_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_engineering_data_project_id ON engineering_data(project_id);

-- Finance data table
CREATE TABLE IF NOT EXISTS finance_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    monthly_revenue DECIMAL(15, 2),
    monthly_cost DECIMAL(15, 2),
    monthly_payment_received DECIMAL(15, 2),
    target_margin DECIMAL(5, 2),
    remarks TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uix_finance_project_year_month UNIQUE (project_id, year, month)
);

CREATE INDEX IF NOT EXISTS ix_finance_data_project_id ON finance_data(project_id);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    department department NOT NULL,
    file_type VARCHAR(50),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_attachments_project_id ON attachments(project_id);
CREATE INDEX IF NOT EXISTS ix_attachments_department ON attachments(department);
"""


async def create_tables():
    """Create all database tables"""
    print("Creating database tables...")

    async with engine.begin() as conn:
        # Execute raw SQL for more control
        for statement in CREATE_TABLES_SQL.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    # Ignore errors for already existing objects
                    if 'already exists' not in str(e).lower():
                        print(f"  Warning: {str(e)[:80]}")

    print("Database tables created successfully!")


async def create_admin_user(username: str, password: str):
    """Create an admin user"""
    from app.utils.security import get_password_hash
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        )
        if result.scalar_one_or_none():
            print(f"User '{username}' already exists!")
            return False

        # Create admin user
        password_hash = get_password_hash(password)
        await session.execute(
            text("""
                INSERT INTO users (username, password_hash, department, is_active)
                VALUES (:username, :password_hash, 'admin', true)
            """),
            {"username": username, "password_hash": password_hash}
        )
        await session.commit()
        print(f"Admin user '{username}' created successfully!")
        return True


async def verify_tables():
    """Verify all tables exist"""
    print("\nVerifying database tables...")

    tables = ['users', 'projects', 'market_data', 'engineering_data', 'finance_data', 'attachments']

    async with engine.begin() as conn:
        for table in tables:
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = :table_name
                    )
                """),
                {"table_name": table}
            )
            exists = result.scalar()
            status = "OK" if exists else "MISSING"
            print(f"  {table}: {status}")

    print("\nDatabase verification complete!")


async def main(create_admin: bool = False):
    """Main entry point"""
    print("=" * 50)
    print("MIS Database Initialization")
    print("=" * 50)

    # Create tables
    await create_tables()

    # Verify tables
    await verify_tables()

    # Optionally create admin user
    if create_admin:
        print("\n" + "=" * 50)
        print("Create Admin User")
        print("=" * 50)
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return

        password = getpass.getpass("Enter admin password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters!")
            return

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match!")
            return

        await create_admin_user(username, password)

    print("\n" + "=" * 50)
    print("Initialization Complete!")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize MIS database")
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create an initial admin user"
    )
    args = parser.parse_args()

    asyncio.run(main(create_admin=args.create_admin))

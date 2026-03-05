"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing types if they exist (for clean re-run)
    op.execute('DROP TYPE IF EXISTS department CASCADE')
    op.execute('DROP TYPE IF EXISTS projectstatus CASCADE')

    # Create department enum
    department_enum = postgresql.ENUM('market', 'engineering', 'finance', 'admin', name='department')
    department_enum.create(op.get_bind(), checkfirst=True)

    # Create project status enum
    status_enum = postgresql.ENUM('planning', 'in_progress', 'completed', 'suspended', name='projectstatus')
    status_enum.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('department', department_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('project_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('construction_unit', sa.String(200), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('contract_start_date', sa.Date(), nullable=True),
        sa.Column('contract_end_date', sa.Date(), nullable=True),
        sa.Column('contract_duration', sa.Integer(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('status', status_enum, default='planning'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create market_data table
    op.create_table(
        'market_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('building_area', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('structure', sa.String(100), nullable=True),
        sa.Column('floors', sa.Integer(), nullable=True),
        sa.Column('contract_value', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('prepayment_ratio', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('advance_amount', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('progress_payment_ratio', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('contract_type', sa.String(100), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'year', 'month', name='uix_market_project_year_month'),
    )

    # Create engineering_data table
    op.create_table(
        'engineering_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        sa.Column('end_period_progress', sa.String(200), nullable=True),
        sa.Column('contract_value', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('monthly_output', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('planned_output', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('monthly_approval', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('staff_count', sa.Integer(), nullable=True),
        sa.Column('next_month_plan', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'year', 'month', name='uix_engineering_project_year_month'),
    )

    # Create finance_data table
    op.create_table(
        'finance_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('monthly_revenue', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('monthly_cost', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('monthly_payment_received', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('target_margin', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'year', 'month', name='uix_finance_project_year_month'),
    )

    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department', department_enum, nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('attachments')
    op.drop_table('finance_data')
    op.drop_table('engineering_data')
    op.drop_table('market_data')
    op.drop_table('projects')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS projectstatus')
    op.execute('DROP TYPE IF EXISTS department')

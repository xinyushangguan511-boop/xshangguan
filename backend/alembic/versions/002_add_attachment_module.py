"""Add attachment module column

Revision ID: 002
Revises: 001
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    attachment_module_enum = postgresql.ENUM(
        'PROJECT', 'MARKET', 'ENGINEERING', 'FINANCE', name='attachmentmodule'
    )
    attachment_module_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'attachments',
        sa.Column(
            'module',
            attachment_module_enum,
            nullable=False,
            server_default=sa.text("'PROJECT'::attachmentmodule"),
        ),
    )
    op.create_index('ix_attachments_module', 'attachments', ['module'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_attachments_module', table_name='attachments')
    op.drop_column('attachments', 'module')
    postgresql.ENUM(name='attachmentmodule').drop(op.get_bind(), checkfirst=True)
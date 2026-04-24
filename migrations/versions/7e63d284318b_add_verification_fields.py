"""Add verification fields

Revision ID: 7e63d284318b
Revises: faa7fcffde72
Create Date: 2026-02-05 19:51:14.180802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e63d284318b'
down_revision: Union[str, Sequence[str], None] = 'faa7fcffde72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False))
    op.add_column('users', sa.Column('verification_token', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')

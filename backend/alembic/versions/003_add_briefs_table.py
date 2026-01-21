"""add briefs table

Revision ID: 003
Revises: 002
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create briefs table
    op.create_table(
        'briefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('article_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('days_range', sa.Integer(), nullable=False, server_default='7'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_briefs_country_code', 'briefs', ['country_code'])
    op.create_index('ix_briefs_generated_at', 'briefs', ['generated_at'])


def downgrade() -> None:
    op.drop_index('ix_briefs_generated_at', table_name='briefs')
    op.drop_index('ix_briefs_country_code', table_name='briefs')
    op.drop_table('briefs')

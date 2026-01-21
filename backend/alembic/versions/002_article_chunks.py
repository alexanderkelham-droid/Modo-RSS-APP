"""article chunks table

Revision ID: 002
Revises: 001
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create article_chunks table with indexes."""
    
    # Create article_chunks table
    op.create_table(
        'article_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('country_codes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('topic_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_article_chunks_article_id', 'article_chunks', ['article_id'])
    op.create_index('idx_article_chunks_article_id_index', 'article_chunks', ['article_id', 'chunk_index'])
    op.create_index('idx_article_chunks_published_at', 'article_chunks', ['published_at'])
    
    # Create GIN indexes for array columns
    op.create_index(
        'idx_article_chunks_country_codes_gin',
        'article_chunks',
        ['country_codes'],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_article_chunks_topic_tags_gin',
        'article_chunks',
        ['topic_tags'],
        postgresql_using='gin'
    )
    
    # Create vector index for similarity search
    # Using IVFFlat for fast approximate nearest neighbor search
    # Note: This should be created after some data exists for better clustering
    # For now, we'll create it but it will be most efficient with data
    op.execute(
        """
        CREATE INDEX idx_article_chunks_embedding_ivfflat 
        ON article_chunks 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    """Drop article_chunks table and indexes."""
    
    op.drop_index('idx_article_chunks_embedding_ivfflat', table_name='article_chunks')
    op.drop_index('idx_article_chunks_topic_tags_gin', table_name='article_chunks')
    op.drop_index('idx_article_chunks_country_codes_gin', table_name='article_chunks')
    op.drop_index('idx_article_chunks_published_at', table_name='article_chunks')
    op.drop_index('idx_article_chunks_article_id_index', table_name='article_chunks')
    op.drop_index('idx_article_chunks_article_id', table_name='article_chunks')
    op.drop_table('article_chunks')

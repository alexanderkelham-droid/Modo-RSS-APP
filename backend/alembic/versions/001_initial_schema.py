"""Initial database schema with sources, articles, and ingestion_runs

Revision ID: 001
Revises: 
Create Date: 2026-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('rss_url', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    
    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('raw_summary', sa.Text(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('hash', sa.String(length=64), nullable=True),
        sa.Column('country_codes', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('topic_tags', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_hash'), 'articles', ['hash'], unique=False)
    op.create_index('idx_articles_published_at', 'articles', ['published_at'], unique=False)
    op.create_index('idx_articles_source_id', 'articles', ['source_id'], unique=False)
    op.create_index('idx_articles_country_codes_gin', 'articles', ['country_codes'], 
                    unique=False, postgresql_using='gin')
    op.create_index('idx_articles_topic_tags_gin', 'articles', ['topic_tags'], 
                    unique=False, postgresql_using='gin')
    
    # Create IVFFlat index for embeddings (requires some data first, so we'll add it later)
    # For now, just note it in comments - will be created after we have some embeddings
    # op.execute('CREATE INDEX idx_articles_embedding_ivfflat ON articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')
    
    # Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingestion_runs_id'), 'ingestion_runs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ingestion_runs_id'), table_name='ingestion_runs')
    op.drop_table('ingestion_runs')
    
    # op.execute('DROP INDEX IF EXISTS idx_articles_embedding_ivfflat')
    op.drop_index('idx_articles_topic_tags_gin', table_name='articles')
    op.drop_index('idx_articles_country_codes_gin', table_name='articles')
    op.drop_index('idx_articles_source_id', table_name='articles')
    op.drop_index('idx_articles_published_at', table_name='articles')
    op.drop_index(op.f('ix_articles_hash'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_table('articles')
    
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    
    op.execute('DROP EXTENSION IF EXISTS vector')

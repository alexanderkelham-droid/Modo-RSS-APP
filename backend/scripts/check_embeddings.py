"""Check if article chunks have embeddings."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.models import Article, ArticleChunk


async def check_embeddings():
    async with AsyncSessionLocal() as db:
        # Count total articles
        article_count = await db.execute(select(func.count()).select_from(Article))
        total_articles = article_count.scalar()
        
        # Count articles with embeddings
        articles_with_embeddings = await db.execute(
            select(func.count()).select_from(Article).where(Article.embedding.isnot(None))
        )
        articles_embedded = articles_with_embeddings.scalar()
        
        # Count total chunks
        chunk_count = await db.execute(select(func.count()).select_from(ArticleChunk))
        total_chunks = chunk_count.scalar()
        
        # Count chunks with embeddings
        chunks_with_embeddings = await db.execute(
            select(func.count()).select_from(ArticleChunk).where(ArticleChunk.embedding.isnot(None))
        )
        chunks_embedded = chunks_with_embeddings.scalar()
        
        print("\n📊 Embedding Status:")
        print("=" * 60)
        print(f"Articles: {articles_embedded}/{total_articles} have embeddings")
        print(f"Chunks: {chunks_embedded}/{total_chunks} have embeddings")
        print("=" * 60)
        
        if chunks_embedded == 0:
            print("\n⚠️  WARNING: No chunks have embeddings!")
            print("You need to run the ingestion pipeline with embedding generation.")
            print("Run: python -m app.ingest.pipeline")
        elif chunks_embedded < total_chunks:
            print(f"\n⚠️  WARNING: Only {chunks_embedded}/{total_chunks} chunks have embeddings")
            print("Some articles may not be searchable in chat.")
        else:
            print("\n✅ All chunks have embeddings - chat should work!")
        
        # Check for recent articles
        recent_query = select(Article.title, Article.published_at).where(
            Article.title.ilike('%hectate%') | Article.title.ilike('%hecate%')
        ).limit(5)
        recent_result = await db.execute(recent_query)
        hecate_articles = recent_result.all()
        
        if hecate_articles:
            print("\n🔍 Found Hecate Energy articles:")
            for article in hecate_articles:
                print(f"  - {article.title[:80]}... ({article.published_at})")
            
            # Check if these have chunks
            for article in hecate_articles:
                chunk_query = select(func.count()).select_from(ArticleChunk).join(Article).where(
                    Article.title == article.title
                )
                chunk_result = await db.execute(chunk_query)
                chunk_count = chunk_result.scalar()
                print(f"    → {chunk_count} chunks")


if __name__ == "__main__":
    asyncio.run(check_embeddings())

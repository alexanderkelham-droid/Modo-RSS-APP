"""
Check if NESO articles are in the database.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.models import Source, Article


async def check_neso_articles():
    """Check NESO articles in database."""
    async with AsyncSessionLocal() as db:
        # Get NESO source
        query = select(Source).where(Source.name == "NESO")
        result = await db.execute(query)
        neso_source = result.scalar_one_or_none()
        
        if not neso_source:
            print("❌ NESO source not found in database")
            return
        
        print(f"✅ NESO source found (ID: {neso_source.id})")
        
        # Count articles for NESO
        count_query = select(func.count(Article.id)).where(Article.source_id == neso_source.id)
        count_result = await db.execute(count_query)
        article_count = count_result.scalar()
        
        print(f"\n📊 NESO articles in database: {article_count}")
        
        if article_count > 0:
            # Get some sample articles
            articles_query = select(Article).where(Article.source_id == neso_source.id).limit(5)
            articles_result = await db.execute(articles_query)
            articles = articles_result.scalars().all()
            
            print(f"\n📰 Sample articles:")
            for article in articles:
                print(f"\n  - {article.title}")
                print(f"    URL: {article.url}")
                print(f"    Published: {article.published_at}")
                print(f"    Countries: {article.country_codes}")
                print(f"    Has content: {'Yes' if article.content_text else 'No'}")
                print(f"    Has embedding: {'Yes' if article.embedding is not None else 'No'}")
        else:
            print("\n⚠️  No NESO articles found in database")
            print("The pipeline scraped articles but failed to save them due to errors.")


if __name__ == "__main__":
    asyncio.run(check_neso_articles())

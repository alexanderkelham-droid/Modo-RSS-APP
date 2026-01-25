"""Delete NESO articles to allow reprocessing with all fixes."""
import asyncio
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.db.models import Source, Article, ArticleChunk


async def main():
    async with AsyncSessionLocal() as db:
        # Get NESO source
        result = await db.execute(select(Source).where(Source.name == "NESO"))
        neso_source = result.scalar_one_or_none()
        
        if not neso_source:
            print("❌ NESO source not found")
            return
        
        print(f"✅ NESO source found (ID: {neso_source.id})")
        
        # Count existing articles
        article_count_query = select(Article).where(Article.source_id == neso_source.id)
        article_result = await db.execute(article_count_query)
        articles = article_result.scalars().all()
        
        print(f"\n📊 Found {len(articles)} NESO articles to delete")
        
        # Delete chunks first (foreign key constraint)
        for article in articles:
            chunk_delete_query = delete(ArticleChunk).where(ArticleChunk.article_id == article.id)
            await db.execute(chunk_delete_query)
        
        # Delete articles
        article_delete_query = delete(Article).where(Article.source_id == neso_source.id)
        await db.execute(article_delete_query)
        
        await db.commit()
        
        print(f"✅ Deleted {len(articles)} NESO articles (and their chunks)")
        print("\nNow run the pipeline again to recreate them with proper tagging and chunking!")


if __name__ == "__main__":
    asyncio.run(main())

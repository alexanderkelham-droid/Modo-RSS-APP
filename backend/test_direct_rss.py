"""Test ingestion from a direct RSS feed (Energy Live News)."""

import asyncio
from app.db.session import get_db
from app.db.models import Source
from app.services.ingest.ingestion_service import IngestionService
from sqlalchemy import select


async def main():
    """Test ingestion from Energy Live News."""
    async for db in get_db():
        # Get Energy Storage News source
        result = await db.execute(
            select(Source).where(Source.name == "Energy Storage News")
        )
        source = result.scalar_one_or_none()
        
        if not source:
            print("❌ Energy Storage News source not found")
            return
        
        print(f"🔄 Testing ingestion from: {source.name}")
        print(f"   URL: {source.rss_url}\n")
        
        # Run ingestion
        from app.services.ingest.ingestion_service import IngestionStats
        service = IngestionService(db)
        stats = IngestionStats()
        await service.ingest_source(source, stats)
        
        print(f"\n✅ Ingestion completed!")
        print(f"   New articles: {stats.new_count}")
        print(f"   Updated: {stats.updated_count}")
        print(f"   Skipped: {stats.skipped_count}")
        print(f"   Extraction failed: {stats.extraction_failed_count}")
        
        # Show sample articles
        result = await db.execute(
            select(source.articles).limit(3)
        )
        articles = result.scalars().all()
        
        print(f"\n📊 Total articles in DB for this source: {len(articles)}")
        print(f"\n📄 Sample articles:")
        for article in articles[:3]:
            print(f"   • {article.title[:80]}...")
            print(f"     Published: {article.published_at}")
            print(f"     Has content: {bool(article.content_text)}")
            if article.content_text:
                print(f"     Content length: {len(article.content_text)} chars")
            print(f"     Countries: {article.country_codes}")
            print(f"     Topics: {article.topic_tags}\n")
        
        break


if __name__ == "__main__":
    asyncio.run(main())

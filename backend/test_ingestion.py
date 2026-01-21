"""Test RSS ingestion without embeddings."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.ingest import IngestionService
from sqlalchemy import select
from app.db.models import Source, Article

async def test_ingestion():
    """Test ingesting from one source without embeddings."""
    async with AsyncSessionLocal() as session:
        # Get first source
        result = await session.execute(
            select(Source).where(Source.enabled == True).limit(1)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            print("❌ No enabled sources found")
            return
        
        print(f"🔄 Testing ingestion from: {source.name}")
        print(f"   URL: {source.rss_url}")
        
        # Create ingestion service
        from app.services.ingest.ingestion_service import IngestionStats
        service = IngestionService(session)
        stats = IngestionStats()
        
        try:
            # Ingest from this source
            await service.ingest_source(source, stats)
            await session.commit()
            
            print(f"\n✅ Ingestion completed!")
            print(f"   New articles: {stats.new_count}")
            print(f"   Updated: {stats.updated_count}")
            print(f"   Skipped: {stats.skipped_count}")
            print(f"   Failed: {len(stats.failed_sources)}")
            print(f"   Extraction failed: {stats.extraction_failed_count}")
            
            # Check articles in database
            result = await session.execute(
                select(Article).where(Article.source_id == source.id)
            )
            articles = result.scalars().all()
            print(f"\n📊 Total articles in DB for this source: {len(articles)}")
            
            if articles:
                print(f"\n📄 Sample articles:")
                for article in articles[:3]:
                    print(f"   • {article.title[:80]}...")
                    print(f"     Published: {article.published_at}")
                    print(f"     Has content: {bool(article.content_text)}")
                    print(f"     Countries: {article.country_codes}")
                    print(f"     Topics: {article.topic_tags}")
                    print()
            
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ingestion())

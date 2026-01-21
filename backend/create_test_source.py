"""Create a test RSS source."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Source
from datetime import datetime, timezone

async def create_test_source():
    """Create a test RSS source."""
    async with AsyncSessionLocal() as session:
        # Check if source already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Source).where(Source.rss_url == "https://www.iea.org/news.xml")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Source already exists: {existing.name} (ID: {existing.id})")
            return existing
        
        # Create new source
        source = Source(
            name="IEA News",
            rss_url="https://www.iea.org/news.xml",
            type="rss",
            enabled=True,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        
        print(f"✅ Created test source: {source.name} (ID: {source.id})")
        return source

if __name__ == "__main__":
    asyncio.run(create_test_source())

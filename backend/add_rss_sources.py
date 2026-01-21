"""Add production RSS sources for energy transition news."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Source
from sqlalchemy import select

# Production RSS sources
SOURCES = [
    {
        "name": "Reuters Energy",
        "rss_url": "https://feeds.reuters.com/reuters/energy",
        "type": "rss",
    },
    {
        "name": "Reuters Environment",
        "rss_url": "https://feeds.reuters.com/reuters/environment",
        "type": "rss",
    },
    {
        "name": "Reuters Sustainability",
        "rss_url": "https://feeds.reuters.com/reuters/sustainability",
        "type": "rss",
    },
    {
        "name": "Renewables Now",
        "rss_url": "https://renewablesnow.com/feed/",
        "type": "rss",
    },
    {
        "name": "Renewable Energy World",
        "rss_url": "https://www.renewableenergyworld.com/feed/",
        "type": "rss",
    },
]

async def add_sources():
    """Add all RSS sources to database."""
    async with AsyncSessionLocal() as session:
        added = 0
        skipped = 0
        
        for source_data in SOURCES:
            # Check if source already exists
            result = await session.execute(
                select(Source).where(Source.rss_url == source_data["rss_url"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⏭️  Skipped (exists): {source_data['name']}")
                skipped += 1
                continue
            
            # Create new source
            source = Source(**source_data, enabled=True)
            session.add(source)
            added += 1
            print(f"✅ Added: {source_data['name']}")
        
        await session.commit()
        print(f"\n📊 Summary: {added} added, {skipped} skipped")

if __name__ == "__main__":
    asyncio.run(add_sources())

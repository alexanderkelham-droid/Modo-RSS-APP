"""Add direct RSS feed sources."""

import asyncio
from app.db.session import get_db
from app.db.models import Source


async def main():
    """Add FT, Energy Live News, and Energy Storage News RSS feeds."""
    async for db in get_db():
        sources = [
            Source(
                name="Financial Times - Energy",
                type="rss",
                rss_url="https://www.ft.com/energy?format=rss",
                enabled=True
            ),
            Source(
                name="Energy Live News",
                type="rss",
                rss_url="https://www.energylivenews.com/feed/",
                enabled=True
            ),
            Source(
                name="Energy Storage News",
                type="rss",
                rss_url="https://www.energy-storage.news/feed/",
                enabled=True
            ),
        ]
        
        for source in sources:
            db.add(source)
            print(f"✅ Added: {source.name}")
            print(f"   URL: {source.rss_url}")
        
        await db.commit()
        
        print(f"\n📊 Total: {len(sources)} direct RSS feeds added")
        break


if __name__ == "__main__":
    asyncio.run(main())

"""Replace sources with Google News RSS feeds for energy topics."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Source
from sqlalchemy import select, delete

# Google News RSS sources with energy keywords
GOOGLE_NEWS_SOURCES = [
    {
        "name": "Google News - Renewable Energy",
        "rss_url": "https://news.google.com/rss/search?q=renewable+energy&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Solar Energy",
        "rss_url": "https://news.google.com/rss/search?q=solar+energy+OR+solar+power&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Wind Energy",
        "rss_url": "https://news.google.com/rss/search?q=wind+energy+OR+wind+power&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Energy Transition",
        "rss_url": "https://news.google.com/rss/search?q=energy+transition&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Climate Change",
        "rss_url": "https://news.google.com/rss/search?q=climate+change+energy&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Electric Vehicles",
        "rss_url": "https://news.google.com/rss/search?q=electric+vehicles+OR+EV&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Hydrogen Energy",
        "rss_url": "https://news.google.com/rss/search?q=hydrogen+energy+OR+green+hydrogen&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Battery Storage",
        "rss_url": "https://news.google.com/rss/search?q=battery+storage+OR+energy+storage&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Carbon Emissions",
        "rss_url": "https://news.google.com/rss/search?q=carbon+emissions+OR+net+zero&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
    {
        "name": "Google News - Reuters Energy",
        "rss_url": "https://news.google.com/rss/search?q=site:reuters.com+energy&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
    },
]

async def replace_sources():
    """Delete old sources and add Google News RSS feeds."""
    async with AsyncSessionLocal() as session:
        # Delete all existing sources
        result = await session.execute(delete(Source))
        deleted = result.rowcount
        print(f"🗑️  Deleted {deleted} old sources")
        
        # Add new Google News sources
        for source_data in GOOGLE_NEWS_SOURCES:
            source = Source(**source_data, enabled=True)
            session.add(source)
            print(f"✅ Added: {source_data['name']}")
        
        await session.commit()
        print(f"\n📊 Total: {len(GOOGLE_NEWS_SOURCES)} Google News feeds configured")

if __name__ == "__main__":
    asyncio.run(replace_sources())

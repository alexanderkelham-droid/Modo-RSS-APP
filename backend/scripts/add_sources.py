"""
Script to add new RSS sources to the database.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Source


async def add_sources():
    """Add new RSS sources to the database."""
    
    sources_to_add = [
        {
            "name": "Carbon Brief",
            "rss_url": "https://www.carbonbrief.org/feed/",
            "enabled": True,
            "type": "rss",
        },
        {
            "name": "Renewable Energy World",
            "rss_url": "https://www.renewableenergyworld.com/feed/",
            "enabled": True,
            "type": "rss",
        },
        {
            "name": "CleanTechnica",
            "rss_url": "https://cleantechnica.com/feed/",
            "enabled": True,
            "type": "rss",
        },
    ]
    
    async with AsyncSessionLocal() as db:
        for source_data in sources_to_add:
            # Check if source already exists
            existing = await db.execute(
                select(Source).where(Source.name == source_data["name"])
            )
            if existing.scalar_one_or_none():
                print(f"⏩ Source '{source_data['name']}' already exists, skipping")
                continue
            
            # Create new source
            source = Source(**source_data)
            db.add(source)
            print(f"✅ Added source: {source_data['name']}")
        
        await db.commit()
        print("\n✨ All sources added successfully!")


if __name__ == "__main__":
    asyncio.run(add_sources())

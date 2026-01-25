"""
Add NESO as a web scraper source.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Source


async def add_neso_source():
    """Add NESO as a web scraper source."""
    async with AsyncSessionLocal() as db:
        # Check if NESO already exists
        query = select(Source).where(Source.name == "NESO")
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ NESO source already exists (ID: {existing.id})")
            return
        
        # Create NESO source
        neso_source = Source(
            name="NESO",
            type="web_scraper",
            rss_url="neso",  # This is the scraper name, not an actual URL
            enabled=True,
        )
        
        db.add(neso_source)
        await db.commit()
        await db.refresh(neso_source)
        
        print(f"✅ Added NESO source (ID: {neso_source.id})")
        print(f"   Name: {neso_source.name}")
        print(f"   Type: {neso_source.type}")
        print(f"   Scraper: {neso_source.rss_url}")
        print(f"   Enabled: {neso_source.enabled}")


if __name__ == "__main__":
    asyncio.run(add_neso_source())

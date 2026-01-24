"""List all sources."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Source


async def list_sources():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Source.name, Source.rss_url, Source.enabled)
            .order_by(Source.name)
        )
        print('\n📰 Current RSS Sources:')
        print('=' * 100)
        for row in result:
            status = '✅' if row.enabled else '❌'
            print(f'{status} {row.name:35} | {row.rss_url}')


if __name__ == "__main__":
    asyncio.run(list_sources())

"""Delete articles to test fresh ingestion with tagging."""

import asyncio
from app.db.session import get_db
from sqlalchemy import delete
from app.db.models import Article


async def main():
    """Delete all articles from Google News source."""
    async for db in get_db():
        # Delete all articles from source 27
        result = await db.execute(
            delete(Article).where(Article.source_id == 27)
        )
        await db.commit()
        
        print(f"✅ Deleted {result.rowcount} articles from Google News - Renewable Energy")
        print("Ready for fresh ingestion test!")
        break


if __name__ == "__main__":
    asyncio.run(main())

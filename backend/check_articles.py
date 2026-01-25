"""Check if specific articles exist."""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Article


async def check_articles():
    async with AsyncSessionLocal() as db:
        # Check for Hecate (correct spelling)
        query = select(Article).where(
            Article.title.ilike('%hecate%')
        )
        result = await db.execute(query)
        hecate = result.scalars().all()
        
        print(f"🔍 Hecate articles: {len(hecate)}")
        for article in hecate:
            print(f"  - {article.title}")


if __name__ == "__main__":
    asyncio.run(check_articles())

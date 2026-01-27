
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Article

async def check_db():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Article).limit(20))
        articles = result.scalars().all()
        for a in articles:
            print(f"Title: {a.title[:50]}...")
            print(f"Countries: {a.country_codes}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_db())

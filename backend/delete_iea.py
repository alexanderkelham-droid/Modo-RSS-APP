"""Delete the IEA News source (404)."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import Source
from sqlalchemy import select

async def delete_iea():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Source).where(Source.name == "IEA News")
        )
        source = result.scalar_one_or_none()
        
        if source:
            await session.delete(source)
            await session.commit()
            print(f"✅ Deleted: {source.name}")
        else:
            print("⏭️  IEA News not found")

asyncio.run(delete_iea())

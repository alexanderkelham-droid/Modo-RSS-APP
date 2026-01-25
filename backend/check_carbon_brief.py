"""Check Carbon Brief articles."""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Article, Source


async def check_carbon_brief():
    async with AsyncSessionLocal() as db:
        # Get Carbon Brief source
        query = select(Source).where(Source.name.ilike('%carbon%'))
        result = await db.execute(query)
        sources = result.scalars().all()
        
        print(f"📰 Sources matching 'carbon': {len(sources)}")
        for source in sources:
            print(f"  - {source.name} (ID: {source.id})")
            
            # Get articles from this source
            query = select(Article).where(
                Article.source_id == source.id
            ).order_by(Article.published_at.desc()).limit(3)
            result = await db.execute(query)
            articles = result.scalars().all()
            
            print(f"\n📄 Recent articles from {source.name}: {len(articles)}")
            for article in articles:
                print(f"\n  Title: {article.title}")
                print(f"  Summary: {article.raw_summary[:100] if article.raw_summary else 'None'}...")
                print(f"  Content preview: {article.content_text[:100] if article.content_text else 'None'}...")


if __name__ == "__main__":
    asyncio.run(check_carbon_brief())

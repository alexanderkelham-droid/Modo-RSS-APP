"""Check ingested articles."""

import asyncio
from app.db.session import get_db
from app.db.models import Article
from sqlalchemy import select


async def main():
    """Check articles from Google News source."""
    async for db in get_db():
        # Get articles from source 27 (Google News - Renewable Energy)
        result = await db.execute(
            select(Article).where(Article.source_id == 27).limit(5)
        )
        articles = result.scalars().all()
        
        print(f"\n📊 Found {len(articles)} articles from Google News - Renewable Energy:\n")
        
        for article in articles:
            print(f"Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"Has content: {bool(article.content_text)}")
            print(f"Content length: {len(article.content_text) if article.content_text else 0} chars")
            print(f"Countries: {article.country_codes}")
            print(f"Topics: {article.topic_tags}")
            print("-" * 80)
        
        break


if __name__ == "__main__":
    asyncio.run(main())

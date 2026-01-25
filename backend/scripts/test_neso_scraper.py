"""
Test NESO web scraper.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ingest.web_scraper import get_scraper


async def test_scraper():
    """Test the NESO web scraper."""
    print("🔍 Testing NESO web scraper...")
    
    # Get scraper
    scraper = get_scraper("neso")
    if not scraper:
        print("❌ Failed to get NESO scraper")
        return
    
    print(f"✅ Got scraper: {scraper.name}")
    print(f"   Base URL: {scraper.base_url}")
    
    # Scrape first page only for testing
    print("\n📰 Scraping articles (1 page)...")
    articles = await scraper.scrape_articles(max_pages=1)
    
    print(f"\n✅ Found {len(articles)} articles")
    
    # Show first 3 articles
    for i, article in enumerate(articles[:3], 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Date: {article.published_at}")
        print(f"Summary: {article.summary[:100]}..." if len(article.summary) > 100 else f"Summary: {article.summary}")


if __name__ == "__main__":
    asyncio.run(test_scraper())

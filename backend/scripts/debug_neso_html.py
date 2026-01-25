"""
Debug NESO HTML structure.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ingest.web_scraper import NESONewsScraper
from bs4 import BeautifulSoup


async def debug_html():
    """Debug NESO HTML structure."""
    scraper = NESONewsScraper()
    
    print("🔍 Fetching NESO news page...")
    html = await scraper.fetch_html(scraper.news_page_url)
    
    # Save to file for inspection
    with open("neso_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Saved HTML to neso_debug.html")
    
    # Parse and show structure
    soup = BeautifulSoup(html, 'lxml')
    
    # Find all links with /news/ in them
    news_links = soup.find_all('a', href=lambda h: h and '/news/' in h and h != '/news-and-events')
    
    print(f"\n📰 Found {len(news_links)} news links")
    
    # Show first few links with their surrounding structure
    for i, link in enumerate(news_links[:3], 1):
        print(f"\n--- Link {i} ---")
        print(f"href: {link.get('href')}")
        print(f"text: {link.get_text(strip=True)[:100]}")
        print(f"classes: {link.get('class', [])}")
        
        # Show parent structure
        parent = link.find_parent()
        if parent:
            print(f"parent tag: {parent.name}")
            print(f"parent classes: {parent.get('class', [])}")
            print(f"parent text (first 150 chars): {parent.get_text(strip=True)[:150]}")


if __name__ == "__main__":
    asyncio.run(debug_html())

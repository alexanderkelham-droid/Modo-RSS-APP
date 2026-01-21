"""Inspect Google News RSS feed structure to find actual article URLs."""

import feedparser
import httpx
import asyncio


async def inspect_google_news_rss():
    """Fetch and inspect Google News RSS feed structure."""
    
    rss_url = "https://news.google.com/rss/search?q=renewable+energy&hl=en-US&gl=US&ceid=US:en"
    
    print(f"📡 Fetching RSS feed: {rss_url}\n")
    
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(rss_url)
        feed_content = response.text
    
    print(f"✅ Got feed ({len(feed_content)} bytes)\n")
    
    # Parse with feedparser
    parsed = feedparser.parse(feed_content)
    
    print(f"📊 Feed has {len(parsed.entries)} entries\n")
    
    # Inspect first entry in detail
    if parsed.entries:
        entry = parsed.entries[0]
        print("=" * 80)
        print("First entry structure:")
        print("=" * 80)
        
        # Print all available fields
        for key in dir(entry):
            if not key.startswith('_'):
                value = getattr(entry, key, None)
                if value and not callable(value):
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 200:
                        str_value = str_value[:200] + "..."
                    print(f"{key}: {str_value}")
        
        print("\n" + "=" * 80)
        print("Looking for actual article URL...")
        print("=" * 80)
        
        # Common fields that might contain actual source URL
        potential_url_fields = ['link', 'links', 'source', 'href', 'id', 'guid']
        
        for field in potential_url_fields:
            if hasattr(entry, field):
                value = getattr(entry, field)
                print(f"\n{field}:")
                print(f"  {value}")
                
                # If it's a list, show each item
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        print(f"  [{i}]: {item}")


if __name__ == "__main__":
    asyncio.run(inspect_google_news_rss())

"""Test Google News URL resolution and content extraction."""

import asyncio
from app.services.ingest.content_extractor import ContentExtractor


async def main():
    """Test URL resolution and extraction."""
    extractor = ContentExtractor()
    
    # Test Google News URL
    test_url = "https://news.google.com/rss/articles/CBMib0FVX3lxTE84SDRlUHJYbzdKX25kYmR3TDFBcEJuN2VsTXpQWVZmRXRTeXItWXo5MGsyZ1JQQWdmZVFZb1BiUXQ4QlhmRy1QVU5uR0RQZFJTelVMWl9sQzBWNjRPSlFvYmFoUDJuMlpjUXZNUmExQQ?oc=5"
    
    print(f"🔍 Testing Google News URL resolution...")
    print(f"Original URL: {test_url}\n")
    
    # Resolve URL
    resolved_url = await extractor.resolve_google_news_url(test_url)
    print(f"✅ Resolved URL: {resolved_url}\n")
    
    # Try to extract content
    try:
        print(f"📄 Attempting content extraction...")
        content, language = await extractor.extract_article(test_url)
        
        if content:
            print(f"✅ Content extracted successfully!")
            print(f"   Language: {language}")
            print(f"   Content length: {len(content)} chars")
            print(f"\n📝 First 500 chars:\n{content[:500]}...")
        else:
            print(f"❌ No content extracted")
            
    except Exception as e:
        print(f"❌ Extraction error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

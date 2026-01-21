"""Test parsing Google News URL to extract actual article URL."""

import asyncio
import httpx
from urllib.parse import unquote


async def test_google_news_parsing():
    """Test different methods to get actual article URL from Google News."""
    
    test_url = "https://news.google.com/rss/articles/CBMib0FVX3lxTE84SDRlUHJYbzdKX25kYmR3TDFBcEJuN2VsTXpQWVZmRXRTeXItWXo5MGsyZ1JQQWdmZVFZb1BiUXQ4QlhmRy1QVU5uR0RQZFJTelVMWl9sQzBWNjRPSlFvYmFoUDJuMlpjUXZNUmExQQ?oc=5"
    
    print(f"Original URL: {test_url}\n")
    
    # Method 1: Try to get the article page (not redirect)
    print("Method 1: Fetch article page HTML directly...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            # Don't follow redirects, get the intermediate page
        }
        
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.get(test_url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Location header: {response.headers.get('location', 'None')}")
            
            # Check if we got HTML
            if 'text/html' in response.headers.get('content-type', ''):
                html = response.text
                print(f"Got HTML ({len(html)} chars)")
                
                # Look for article URL in the HTML
                if 'window.location' in html:
                    print("Found window.location redirect")
                if 'meta http-equiv' in html:
                    print("Found meta redirect")
                    
                # Search for article link patterns
                import re
                # Look for actual article URLs (common news domains)
                url_patterns = [
                    r'https?://(?:www\.)?(wired|bbc|cnn|reuters|bloomberg|ft|theguardian|nytimes|washingtonpost)\.com[^\s"\'<>]+',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        print(f"\n✅ Found article URLs:")
                        for match in matches[:3]:
                            print(f"   {match}")
                        break
                
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Check RSS entry structure
    print("\n\nMethod 2: Check if RSS feed has actual links...")
    print("The RSS feed itself might have the actual article URL in a different field")


if __name__ == "__main__":
    asyncio.run(test_google_news_parsing())

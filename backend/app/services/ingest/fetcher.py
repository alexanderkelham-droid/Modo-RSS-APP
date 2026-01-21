"""
HTTP client utilities for fetching RSS feeds.
"""

import httpx
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.settings import settings


class FeedFetchError(Exception):
    """Raised when feed fetching fails."""
    pass


class RSSFetcher:
    """HTTP client for fetching RSS feeds with retry logic."""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize RSS fetcher.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or settings.USER_AGENT
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def fetch_feed(self, url: str) -> str:
        """
        Fetch RSS feed content from URL with retries.
        
        Args:
            url: RSS feed URL
            
        Returns:
            Raw feed content as string
            
        Raises:
            FeedFetchError: If fetch fails after retries
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            raise FeedFetchError(f"HTTP {e.response.status_code}: {url}") from e
        except httpx.TimeoutException as e:
            raise FeedFetchError(f"Timeout fetching {url}") from e
        except httpx.HTTPError as e:
            raise FeedFetchError(f"HTTP error fetching {url}: {e}") from e
        except Exception as e:
            raise FeedFetchError(f"Unexpected error fetching {url}: {e}") from e

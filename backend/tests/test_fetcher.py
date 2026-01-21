"""
Tests for RSS fetcher with mocked HTTP.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.services.ingest.fetcher import RSSFetcher, FeedFetchError


@pytest.mark.asyncio
async def test_fetch_feed_success():
    """Test successful feed fetch."""
    fetcher = RSSFetcher(timeout=10)
    
    mock_response = AsyncMock()
    mock_response.text = "<rss>test content</rss>"
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await fetcher.fetch_feed("https://example.com/feed.xml")
        
        assert result == "<rss>test content</rss>"


@pytest.mark.asyncio
async def test_fetch_feed_timeout():
    """Test feed fetch with timeout."""
    fetcher = RSSFetcher(timeout=5, max_retries=1)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        with pytest.raises(FeedFetchError, match="Timeout"):
            await fetcher.fetch_feed("https://example.com/feed.xml")


@pytest.mark.asyncio
async def test_fetch_feed_http_error():
    """Test feed fetch with HTTP error."""
    fetcher = RSSFetcher(timeout=10, max_retries=1)
    
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.raise_for_status = AsyncMock(
        side_effect=httpx.HTTPStatusError("Not found", request=None, response=mock_response)
    )
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(FeedFetchError, match="HTTP 404"):
            await fetcher.fetch_feed("https://example.com/feed.xml")


@pytest.mark.asyncio
async def test_fetch_feed_with_redirects():
    """Test feed fetch follows redirects."""
    fetcher = RSSFetcher(timeout=10)
    
    mock_response = AsyncMock()
    mock_response.text = "<rss>redirected content</rss>"
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await fetcher.fetch_feed("https://example.com/feed.xml")
        
        # Verify follow_redirects was passed
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get('follow_redirects') is True
        
        assert result == "<rss>redirected content</rss>"


@pytest.mark.asyncio
async def test_fetch_feed_custom_user_agent():
    """Test feed fetch with custom user agent."""
    fetcher = RSSFetcher(timeout=10, user_agent="TestBot/1.0")
    
    mock_response = AsyncMock()
    mock_response.text = "<rss>content</rss>"
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        await fetcher.fetch_feed("https://example.com/feed.xml")
        
        # Check that User-Agent header was set
        call_kwargs = mock_get.call_args.kwargs
        headers = call_kwargs.get('headers', {})
        assert headers.get('User-Agent') == "TestBot/1.0"

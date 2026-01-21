"""
Integration tests for countries API endpoint.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_list_countries_empty(test_db, async_client: AsyncClient):
    """Test listing countries when no articles exist."""
    response = await async_client.get("/countries")
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_articles"] == 0


@pytest.mark.asyncio
async def test_list_countries_basic(test_db, async_client: AsyncClient):
    """Test basic country listing."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        
        # Create articles for different countries
        article1 = Article(
            source_id=source.id,
            title="US Article 1",
            url="https://test.com/us1",
            content_hash="hash1",
            published_at=now - timedelta(days=1),
            country_codes=["US"],
        )
        article2 = Article(
            source_id=source.id,
            title="US Article 2",
            url="https://test.com/us2",
            content_hash="hash2",
            published_at=now - timedelta(days=2),
            country_codes=["US"],
        )
        article3 = Article(
            source_id=source.id,
            title="UK Article",
            url="https://test.com/uk",
            content_hash="hash3",
            published_at=now - timedelta(days=1),
            country_codes=["GB"],
        )
        db.add_all([article1, article2, article3])
        await db.commit()
    
    response = await async_client.get("/countries")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total_articles"] == 3
    
    # Check sorting (by count descending)
    assert data["items"][0]["country_code"] == "US"
    assert data["items"][0]["article_count"] == 2
    assert data["items"][1]["country_code"] == "GB"
    assert data["items"][1]["article_count"] == 1


@pytest.mark.asyncio
async def test_list_countries_date_filter(test_db, async_client: AsyncClient):
    """Test country listing respects date filter."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        
        # Recent article
        article1 = Article(
            source_id=source.id,
            title="Recent",
            url="https://test.com/recent",
            content_hash="hash1",
            published_at=now - timedelta(days=2),
            country_codes=["US"],
        )
        # Old article
        article2 = Article(
            source_id=source.id,
            title="Old",
            url="https://test.com/old",
            content_hash="hash2",
            published_at=now - timedelta(days=30),
            country_codes=["GB"],
        )
        db.add_all([article1, article2])
        await db.commit()
    
    # Query last 7 days
    response = await async_client.get("/countries?days=7")
    
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["country_code"] == "US"


@pytest.mark.asyncio
async def test_list_countries_multiple_codes(test_db, async_client: AsyncClient):
    """Test articles with multiple country codes."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        
        # Article tagged with multiple countries
        article = Article(
            source_id=source.id,
            title="Multi-country",
            url="https://test.com/multi",
            content_hash="hash1",
            published_at=now - timedelta(days=1),
            country_codes=["US", "GB", "DE"],
        )
        db.add(article)
        await db.commit()
    
    response = await async_client.get("/countries")
    
    data = response.json()
    assert len(data["items"]) == 3
    # Each country should have count of 1
    for item in data["items"]:
        assert item["article_count"] == 1


@pytest.mark.asyncio
async def test_list_countries_ignores_null(test_db, async_client: AsyncClient):
    """Test that articles without country codes are ignored."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        
        # Article with countries
        article1 = Article(
            source_id=source.id,
            title="With country",
            url="https://test.com/with",
            content_hash="hash1",
            published_at=now - timedelta(days=1),
            country_codes=["US"],
        )
        # Article without countries
        article2 = Article(
            source_id=source.id,
            title="No country",
            url="https://test.com/without",
            content_hash="hash2",
            published_at=now - timedelta(days=1),
            country_codes=None,
        )
        db.add_all([article1, article2])
        await db.commit()
    
    response = await async_client.get("/countries")
    
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total_articles"] == 1


@pytest.mark.asyncio
async def test_list_countries_name_resolution(test_db, async_client: AsyncClient):
    """Test that country codes are resolved to names."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        
        article = Article(
            source_id=source.id,
            title="Article",
            url="https://test.com/article",
            content_hash="hash1",
            published_at=now - timedelta(days=1),
            country_codes=["GB"],
        )
        db.add(article)
        await db.commit()
    
    response = await async_client.get("/countries")
    
    data = response.json()
    assert data["items"][0]["country_code"] == "GB"
    assert data["items"][0]["country_name"] == "United Kingdom"

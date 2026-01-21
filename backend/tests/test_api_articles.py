"""
Integration tests for articles API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_list_articles_empty(test_db, async_client: AsyncClient):
    """Test listing articles when database is empty."""
    response = await async_client.get("/articles")
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["has_next"] is False


@pytest.mark.asyncio
async def test_list_articles_basic(test_db, async_client: AsyncClient):
    """Test basic article listing."""
    async with test_db() as db:
        # Create source
        source = Source(name="Test Source", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create articles
        now = datetime.utcnow()
        for i in range(5):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/article{i}",
                content_hash=f"hash{i}",
                published_at=now - timedelta(days=i),
                country_codes=["US"],
                topic_tags=["renewables_solar"],
            )
            db.add(article)
        await db.commit()
    
    response = await async_client.get("/articles")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 5
    assert data["page"] == 1
    
    # Check ordering (newest first)
    assert data["items"][0]["title"] == "Article 0"


@pytest.mark.asyncio
async def test_list_articles_country_filter(test_db, async_client: AsyncClient):
    """Test filtering articles by country."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # US article
        article1 = Article(
            source_id=source.id,
            title="US Article",
            url="https://test.com/us",
            content_hash="hash1",
            published_at=datetime.utcnow(),
            country_codes=["US"],
        )
        # UK article
        article2 = Article(
            source_id=source.id,
            title="UK Article",
            url="https://test.com/uk",
            content_hash="hash2",
            published_at=datetime.utcnow(),
            country_codes=["GB"],
        )
        db.add_all([article1, article2])
        await db.commit()
    
    response = await async_client.get("/articles?country=US")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "US Article"


@pytest.mark.asyncio
async def test_list_articles_topic_filter(test_db, async_client: AsyncClient):
    """Test filtering articles by topic."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article1 = Article(
            source_id=source.id,
            title="Solar Article",
            url="https://test.com/solar",
            content_hash="hash1",
            published_at=datetime.utcnow(),
            topic_tags=["renewables_solar"],
        )
        article2 = Article(
            source_id=source.id,
            title="Wind Article",
            url="https://test.com/wind",
            content_hash="hash2",
            published_at=datetime.utcnow(),
            topic_tags=["renewables_wind"],
        )
        db.add_all([article1, article2])
        await db.commit()
    
    response = await async_client.get("/articles?topic=renewables_solar")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Solar Article"


@pytest.mark.asyncio
async def test_list_articles_pagination(test_db, async_client: AsyncClient):
    """Test article pagination."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create 25 articles
        now = datetime.utcnow()
        for i in range(25):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/{i}",
                content_hash=f"hash{i}",
                published_at=now - timedelta(hours=i),
            )
            db.add(article)
        await db.commit()
    
    # Page 1
    response = await async_client.get("/articles?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["has_next"] is True
    assert data["has_prev"] is False
    
    # Page 2
    response = await async_client.get("/articles?page=2&page_size=10")
    data = response.json()
    assert len(data["items"]) == 10
    assert data["has_next"] is True
    assert data["has_prev"] is True


@pytest.mark.asyncio
async def test_top_stories_basic(test_db, async_client: AsyncClient):
    """Test top stories endpoint."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create articles with different recency
        now = datetime.utcnow()
        article1 = Article(
            source_id=source.id,
            title="Recent announcement",
            url="https://reuters.com/article1",
            content_hash="hash1",
            published_at=now - timedelta(hours=1),
            country_codes=["GB"],
            content_text="Big policy announcement today",
        )
        article2 = Article(
            source_id=source.id,
            title="Old news",
            url="https://test.com/article2",
            content_hash="hash2",
            published_at=now - timedelta(days=6),
            country_codes=["GB"],
            content_text="Some content",
        )
        db.add_all([article1, article2])
        await db.commit()
    
    response = await async_client.get("/articles/top-stories?country=GB&days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["country"] == "GB"
    
    # Recent announcement should rank higher
    assert data["items"][0]["title"] == "Recent announcement"
    assert data["items"][0]["score"] > data["items"][1]["score"]


@pytest.mark.asyncio
async def test_top_stories_keyword_boost(test_db, async_client: AsyncClient):
    """Test that priority keywords boost ranking."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        # Both recent, but one has priority keywords
        article1 = Article(
            source_id=source.id,
            title="Regular news",
            url="https://test.com/article1",
            content_hash="hash1",
            published_at=now - timedelta(hours=1),
            country_codes=["US"],
            content_text="Some regular content",
        )
        article2 = Article(
            source_id=source.id,
            title="Major policy announcement",
            url="https://test.com/article2",
            content_hash="hash2",
            published_at=now - timedelta(hours=2),
            country_codes=["US"],
            content_text="Investment breakthrough funding",
        )
        db.add_all([article1, article2])
        await db.commit()
    
    response = await async_client.get("/articles/top-stories?country=US")
    
    data = response.json()
    # Article with keywords should rank higher despite being slightly older
    assert data["items"][0]["title"] == "Major policy announcement"


@pytest.mark.asyncio
async def test_top_stories_limit(test_db, async_client: AsyncClient):
    """Test top stories respects limit parameter."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        for i in range(20):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/{i}",
                content_hash=f"hash{i}",
                published_at=now - timedelta(hours=i),
                country_codes=["DE"],
            )
            db.add(article)
        await db.commit()
    
    response = await async_client.get("/articles/top-stories?country=DE&limit=5")
    
    data = response.json()
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_top_stories_no_results(test_db, async_client: AsyncClient):
    """Test top stories with no matching articles."""
    response = await async_client.get("/articles/top-stories?country=XX")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0

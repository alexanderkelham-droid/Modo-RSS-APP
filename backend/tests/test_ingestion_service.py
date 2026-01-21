"""
Tests for ingestion service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.services.ingest.ingestion_service import IngestionService, IngestionStats
from app.services.ingest.rss_parser import RSSEntry
from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_get_enabled_sources(test_db):
    """Test fetching enabled sources."""
    # Create test sources
    source1 = Source(name="Source 1", type="rss", rss_url="https://example.com/feed1.xml", enabled=True)
    source2 = Source(name="Source 2", type="rss", rss_url="https://example.com/feed2.xml", enabled=False)
    source3 = Source(name="Source 3", type="rss", rss_url="https://example.com/feed3.xml", enabled=True)
    
    test_db.add_all([source1, source2, source3])
    await test_db.commit()
    
    # Test service
    service = IngestionService(test_db)
    sources = await service.get_enabled_sources()
    
    assert len(sources) == 2
    assert all(s.enabled for s in sources)
    assert {s.name for s in sources} == {"Source 1", "Source 3"}


@pytest.mark.asyncio
async def test_upsert_article_new(test_db):
    """Test inserting a new article."""
    # Create source
    source = Source(name="Test Source", type="rss", rss_url="https://example.com/feed.xml", enabled=True)
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Create entry
    entry = RSSEntry(
        title="New Article",
        url="https://example.com/article-1",
        published_at=datetime(2026, 1, 20, 10, 0, 0),
        summary="Test summary"
    )
    
    # Upsert
    service = IngestionService(test_db)
    inserted, updated = await service.upsert_article(source.id, entry)
    await test_db.commit()
    
    assert inserted is True
    assert updated is False
    
    # Verify article was created
    from sqlalchemy import select
    result = await test_db.execute(select(Article).where(Article.url == entry.url))
    article = result.scalar_one()
    
    assert article.title == "New Article"
    assert article.source_id == source.id
    assert article.raw_summary == "Test summary"


@pytest.mark.asyncio
async def test_upsert_article_update(test_db):
    """Test updating an existing article."""
    # Create source and article
    source = Source(name="Test Source", type="rss", rss_url="https://example.com/feed.xml", enabled=True)
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    article = Article(
        source_id=source.id,
        title="Original Title",
        url="https://example.com/article-1",
        raw_summary="Original summary",
        hash="oldhash"
    )
    test_db.add(article)
    await test_db.commit()
    
    # Create updated entry
    entry = RSSEntry(
        title="Updated Title",
        url="https://example.com/article-1",
        published_at=datetime(2026, 1, 20, 10, 0, 0),
        summary="Updated summary"
    )
    
    # Upsert
    service = IngestionService(test_db)
    inserted, updated = await service.upsert_article(source.id, entry)
    await test_db.commit()
    
    assert inserted is False
    assert updated is True
    
    # Verify article was updated
    await test_db.refresh(article)
    assert article.title == "Updated Title"
    assert article.raw_summary == "Updated summary"


@pytest.mark.asyncio
async def test_upsert_article_skip_unchanged(test_db):
    """Test skipping unchanged article."""
    # Create source
    source = Source(name="Test Source", type="rss", rss_url="https://example.com/feed.xml", enabled=True)
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Create entry and compute its hash
    entry = RSSEntry(
        title="Test Article",
        url="https://example.com/article-1",
        summary="Test summary"
    )
    
    service = IngestionService(test_db)
    content_hash = service.parser.compute_content_hash(entry.title, entry.url, entry.summary)
    
    # Create article with same hash
    article = Article(
        source_id=source.id,
        title=entry.title,
        url=entry.url,
        raw_summary=entry.summary,
        hash=content_hash
    )
    test_db.add(article)
    await test_db.commit()
    
    # Try to upsert same content
    inserted, updated = await service.upsert_article(source.id, entry)
    
    assert inserted is False
    assert updated is False


@pytest.mark.asyncio
async def test_ingestion_stats():
    """Test ingestion statistics tracking."""
    stats = IngestionStats()
    
    stats.new_count = 5
    stats.updated_count = 2
    stats.skipped_count = 3
    stats.failed_sources.append({
        "source_id": 1,
        "source_name": "Failed Source",
        "error": "Connection error"
    })
    
    result = stats.to_dict()
    
    assert result["new"] == 5
    assert result["updated"] == 2
    assert result["skipped"] == 3
    assert len(result["failed_sources"]) == 1
    assert result["total_sources"] == 11  # 5+2+3+1


@pytest.mark.asyncio
async def test_ingest_source_success(test_db):
    """Test successful source ingestion."""
    # Create source
    source = Source(name="Test Source", type="rss", rss_url="https://example.com/feed.xml", enabled=True)
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Mock fetcher and parser
    feed_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Article 1</title>
                <link>https://example.com/article-1</link>
                <description>Summary 1</description>
            </item>
        </channel>
    </rss>"""
    
    service = IngestionService(test_db)
    service.fetcher.fetch_feed = AsyncMock(return_value=feed_xml)
    
    stats = IngestionStats()
    await service.ingest_source(source, stats)
    
    assert stats.new_count == 1
    assert stats.updated_count == 0
    assert len(stats.failed_sources) == 0

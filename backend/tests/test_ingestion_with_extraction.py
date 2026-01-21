"""
Integration test for ingestion with content extraction.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.ingest.ingestion_service import IngestionService, IngestionStats
from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_ingest_source_with_extraction(test_db):
    """Test source ingestion with content extraction."""
    # Create non-paywalled source
    source = Source(
        name="Test Source",
        type="rss",
        rss_url="https://example.com/feed.xml",
        enabled=True
    )
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Mock RSS feed
    feed_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Solar Energy Article</title>
                <link>https://example.com/article-1</link>
                <description>Brief summary</description>
            </item>
        </channel>
    </rss>"""
    
    # Mock article HTML
    article_html = """
    <html>
    <body>
        <article>
            <p>This is the full article content about solar energy.</p>
            <p>It contains multiple paragraphs with substantial information.</p>
            <p>Solar panels are becoming more efficient every year.</p>
        </article>
    </body>
    </html>
    """
    
    service = IngestionService(test_db)
    service.fetcher.fetch_feed = AsyncMock(return_value=feed_xml)
    service.extractor.fetch_html = AsyncMock(return_value=article_html)
    
    stats = IngestionStats()
    await service.ingest_source(source, stats)
    
    # Verify article was created with content
    from sqlalchemy import select
    result = await test_db.execute(
        select(Article).where(Article.url == "https://example.com/article-1")
    )
    article = result.scalar_one()
    
    assert article is not None
    assert article.title == "Solar Energy Article"
    assert article.content_text is not None
    assert "solar energy" in article.content_text.lower()
    assert article.language == "en"
    assert stats.new_count == 1
    assert stats.extraction_failed_count == 0


@pytest.mark.asyncio
async def test_ingest_paywalled_source_skip_extraction(test_db):
    """Test that paywalled sources skip content extraction."""
    # Create paywalled source
    source = Source(
        name="Paywalled Source",
        type="paywalled",
        rss_url="https://example.com/feed.xml",
        enabled=True
    )
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Mock RSS feed
    feed_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Premium Article</title>
                <link>https://example.com/premium-article</link>
                <description>Premium content summary</description>
            </item>
        </channel>
    </rss>"""
    
    service = IngestionService(test_db)
    service.fetcher.fetch_feed = AsyncMock(return_value=feed_xml)
    # extractor should NOT be called for paywalled sources
    service.extractor.fetch_html = AsyncMock()
    
    stats = IngestionStats()
    await service.ingest_source(source, stats)
    
    # Verify article was created without content extraction
    from sqlalchemy import select
    result = await test_db.execute(
        select(Article).where(Article.url == "https://example.com/premium-article")
    )
    article = result.scalar_one()
    
    assert article is not None
    assert article.title == "Premium Article"
    assert article.content_text is None  # No extraction for paywalled
    assert stats.new_count == 1
    
    # Verify extractor was not called
    service.extractor.fetch_html.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_extraction_failure_continues(test_db):
    """Test that extraction failures don't stop ingestion."""
    source = Source(
        name="Test Source",
        type="rss",
        rss_url="https://example.com/feed.xml",
        enabled=True
    )
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    
    # Mock RSS feed with one article
    feed_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Article Title</title>
                <link>https://example.com/article-1</link>
                <description>Summary</description>
            </item>
        </channel>
    </rss>"""
    
    service = IngestionService(test_db)
    service.fetcher.fetch_feed = AsyncMock(return_value=feed_xml)
    
    # Mock extraction failure
    from app.services.ingest.content_extractor import ContentExtractionError
    service.extractor.extract_article = AsyncMock(
        side_effect=ContentExtractionError("Timeout")
    )
    
    stats = IngestionStats()
    await service.ingest_source(source, stats)
    
    # Article should still be created, just without content
    from sqlalchemy import select
    result = await test_db.execute(
        select(Article).where(Article.url == "https://example.com/article-1")
    )
    article = result.scalar_one()
    
    assert article is not None
    assert article.content_text is None
    assert stats.new_count == 1
    assert stats.extraction_failed_count == 1

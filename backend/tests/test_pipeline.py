"""
Tests for ingestion pipeline.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.ingest.pipeline import run_full_ingestion_pipeline, IngestionMetrics
from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_ingestion_metrics():
    """Test IngestionMetrics tracking."""
    metrics = IngestionMetrics()
    
    metrics.sources_processed = 2
    metrics.articles_new = 5
    metrics.chunks_created = 15
    metrics.errors.append("Test error")
    
    result = metrics.to_dict()
    
    assert result["sources_processed"] == 2
    assert result["articles_new"] == 5
    assert result["chunks_created"] == 15
    assert result["errors"] == 1
    assert "duration_seconds" in result
    assert "start_time" in result


@pytest.mark.asyncio
async def test_pipeline_no_sources(test_db):
    """Test pipeline with no enabled sources."""
    async with test_db as db:
        # No sources in database
        pass
    
    with patch('app.ingest.pipeline.async_session_maker', return_value=test_db):
        metrics = await run_full_ingestion_pipeline()
    
    assert metrics["sources_processed"] == 0
    assert metrics["articles_new"] == 0


@pytest.mark.asyncio
async def test_pipeline_with_source(test_db):
    """Test pipeline with one source."""
    async with test_db as db:
        source = Source(
            name="Test Source",
            rss_url="https://test.com/rss",
            enabled=True
        )
        db.add(source)
        await db.commit()
    
    # Mock fetcher and parser
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch.return_value = "<rss>test</rss>"
    
    mock_parser = MagicMock()
    mock_parser.parse.return_value = [
        {
            "title": "Test Article",
            "url": "https://test.com/article",
            "content_hash": "hash123",
            "published_at": datetime.utcnow(),
            "summary": "Test summary"
        }
    ]
    
    # Mock extractor
    mock_extractor = AsyncMock()
    mock_extractor.extract.return_value = {
        "content": "Test content",
        "language": "en"
    }
    
    # Mock taggers
    mock_country_tagger = MagicMock()
    mock_country_tagger.tag.return_value = [{"code": "US"}]
    
    mock_topic_tagger = MagicMock()
    mock_topic_tagger.tag.return_value = [{"topic_id": "renewables_solar"}]
    
    # Mock chunking
    mock_chunking = MagicMock()
    mock_chunking.chunk_article.return_value = [
        {"chunk_index": 0, "text": "Chunk 1", "char_count": 7}
    ]
    
    # Mock embeddings
    mock_embeddings = AsyncMock()
    mock_embeddings.embed_batch.return_value = [[0.1] * 1536]
    
    with patch('app.ingest.pipeline.async_session_maker', return_value=test_db), \
         patch('app.ingest.pipeline.RSSFetcher', return_value=mock_fetcher), \
         patch('app.ingest.pipeline.RSSParser', return_value=mock_parser), \
         patch('app.ingest.pipeline.ContentExtractor', return_value=mock_extractor), \
         patch('app.ingest.pipeline.CountryTagger', return_value=mock_country_tagger), \
         patch('app.ingest.pipeline.TopicTagger', return_value=mock_topic_tagger), \
         patch('app.ingest.pipeline.ChunkingService', return_value=mock_chunking), \
         patch('app.ingest.pipeline.OpenAIEmbeddingProvider', return_value=mock_embeddings):
        
        metrics = await run_full_ingestion_pipeline()
    
    assert metrics["sources_processed"] == 1
    assert metrics["articles_fetched"] == 1
    assert metrics["articles_new"] == 1
    assert metrics["articles_extracted"] == 1
    assert metrics["articles_tagged"] == 1
    assert metrics["chunks_created"] == 1
    assert metrics["chunks_embedded"] == 1


@pytest.mark.asyncio
async def test_pipeline_handles_errors(test_db):
    """Test pipeline error handling."""
    async with test_db as db:
        source = Source(
            name="Test Source",
            rss_url="https://test.com/rss",
            enabled=True
        )
        db.add(source)
        await db.commit()
    
    # Mock fetcher to raise error
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch.side_effect = Exception("Network error")
    
    with patch('app.ingest.pipeline.async_session_maker', return_value=test_db), \
         patch('app.ingest.pipeline.RSSFetcher', return_value=mock_fetcher):
        
        metrics = await run_full_ingestion_pipeline()
    
    assert metrics["sources_processed"] == 1
    assert metrics["errors"] > 0
    assert any("Network error" in str(e) for e in metrics["error_details"])


@pytest.mark.asyncio
async def test_pipeline_skips_existing_with_content(test_db):
    """Test pipeline skips articles that already have content."""
    async with test_db as db:
        source = Source(
            name="Test Source",
            rss_url="https://test.com/rss",
            enabled=True
        )
        db.add(source)
        await db.flush()
        
        # Create existing article with content
        article = Article(
            source_id=source.id,
            title="Existing Article",
            url="https://test.com/article",
            content_hash="hash123",
            content_text="Existing content",
        )
        db.add(article)
        await db.commit()
    
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch.return_value = "<rss>test</rss>"
    
    mock_parser = MagicMock()
    mock_parser.parse.return_value = [
        {
            "title": "Existing Article",
            "url": "https://test.com/article",
            "content_hash": "hash123",
            "published_at": datetime.utcnow(),
        }
    ]
    
    with patch('app.ingest.pipeline.async_session_maker', return_value=test_db), \
         patch('app.ingest.pipeline.RSSFetcher', return_value=mock_fetcher), \
         patch('app.ingest.pipeline.RSSParser', return_value=mock_parser):
        
        metrics = await run_full_ingestion_pipeline()
    
    # Should fetch but not process (already has content)
    assert metrics["articles_fetched"] == 1
    assert metrics["articles_extracted"] == 0


@pytest.mark.asyncio
async def test_pipeline_chunks_without_embeddings_on_error(test_db):
    """Test pipeline saves chunks even if embeddings fail."""
    async with test_db as db:
        source = Source(
            name="Test Source",
            rss_url="https://test.com/rss",
            enabled=True
        )
        db.add(source)
        await db.commit()
    
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch.return_value = "<rss>test</rss>"
    
    mock_parser = MagicMock()
    mock_parser.parse.return_value = [
        {
            "title": "Test Article",
            "url": "https://test.com/article",
            "content_hash": "hash123",
            "published_at": datetime.utcnow(),
        }
    ]
    
    mock_extractor = AsyncMock()
    mock_extractor.extract.return_value = {
        "content": "Test content",
        "language": "en"
    }
    
    mock_country_tagger = MagicMock()
    mock_country_tagger.tag.return_value = []
    
    mock_topic_tagger = MagicMock()
    mock_topic_tagger.tag.return_value = []
    
    mock_chunking = MagicMock()
    mock_chunking.chunk_article.return_value = [
        {"chunk_index": 0, "text": "Chunk 1", "char_count": 7}
    ]
    
    # Mock embeddings to fail
    mock_embeddings = AsyncMock()
    mock_embeddings.embed_batch.side_effect = Exception("API rate limit")
    
    with patch('app.ingest.pipeline.async_session_maker', return_value=test_db), \
         patch('app.ingest.pipeline.RSSFetcher', return_value=mock_fetcher), \
         patch('app.ingest.pipeline.RSSParser', return_value=mock_parser), \
         patch('app.ingest.pipeline.ContentExtractor', return_value=mock_extractor), \
         patch('app.ingest.pipeline.CountryTagger', return_value=mock_country_tagger), \
         patch('app.ingest.pipeline.TopicTagger', return_value=mock_topic_tagger), \
         patch('app.ingest.pipeline.ChunkingService', return_value=mock_chunking), \
         patch('app.ingest.pipeline.OpenAIEmbeddingProvider', return_value=mock_embeddings):
        
        metrics = await run_full_ingestion_pipeline()
    
    # Should create chunks but not embed them
    assert metrics["chunks_created"] == 1
    assert metrics["chunks_embedded"] == 0

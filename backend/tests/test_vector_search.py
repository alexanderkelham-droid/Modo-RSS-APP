"""
Tests for vector search service.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.db.models import Article, ArticleChunk, Source
from app.services.rag.vector_search import VectorSearchService, SearchFilters
from app.services.rag.embedding_provider import FakeEmbeddingProvider


@pytest.mark.asyncio
async def test_search_basic(test_db):
    """Test basic vector search."""
    async with test_db() as db:
        # Create test data
        source = Source(
            name="Test Source",
            url="https://test.com/rss",
            enabled=True
        )
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Solar energy breakthrough",
            url="https://test.com/article1",
            content_hash="hash1",
            published_at=datetime.utcnow(),
            country_codes=["US"],
            topic_tags=["renewables_solar"],
        )
        db.add(article)
        await db.flush()
        
        # Create chunk with fake embedding
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["solar energy innovation"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="Solar energy innovation is accelerating.",
            embedding=embeddings[0],
            country_codes=["US"],
            topic_tags=["renewables_solar"],
            published_at=article.published_at,
        )
        db.add(chunk)
        await db.commit()
        
        # Search
        search_service = VectorSearchService(provider)
        results = await search_service.search(db, "solar energy", k=5)
        
        assert len(results) == 1
        assert results[0].article_title == "Solar energy breakthrough"
        assert results[0].chunk_text == "Solar energy innovation is accelerating."
        assert results[0].similarity > 0.5  # Should be high similarity


@pytest.mark.asyncio
async def test_search_with_country_filter(test_db):
    """Test search with country filter."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create articles with different countries
        article1 = Article(
            source_id=source.id,
            title="US solar",
            url="https://test.com/1",
            content_hash="hash1",
            country_codes=["US"],
            topic_tags=["renewables_solar"],
        )
        article2 = Article(
            source_id=source.id,
            title="Germany solar",
            url="https://test.com/2",
            content_hash="hash2",
            country_codes=["DE"],
            topic_tags=["renewables_solar"],
        )
        db.add_all([article1, article2])
        await db.flush()
        
        # Create chunks
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["solar energy", "solar power"])
        
        chunk1 = ArticleChunk(
            article_id=article1.id,
            chunk_index=0,
            text="US solar energy",
            embedding=embeddings[0],
            country_codes=["US"],
            topic_tags=["renewables_solar"],
        )
        chunk2 = ArticleChunk(
            article_id=article2.id,
            chunk_index=0,
            text="Germany solar power",
            embedding=embeddings[1],
            country_codes=["DE"],
            topic_tags=["renewables_solar"],
        )
        db.add_all([chunk1, chunk2])
        await db.commit()
        
        # Search with US filter
        search_service = VectorSearchService(provider)
        filters = SearchFilters(countries=["US"])
        results = await search_service.search(db, "solar", filters=filters, k=5)
        
        assert len(results) == 1
        assert results[0].article_title == "US solar"


@pytest.mark.asyncio
async def test_search_with_topic_filter(test_db):
    """Test search with topic filter."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create articles with different topics
        article1 = Article(
            source_id=source.id,
            title="Solar article",
            url="https://test.com/1",
            content_hash="hash1",
            topic_tags=["renewables_solar"],
        )
        article2 = Article(
            source_id=source.id,
            title="Wind article",
            url="https://test.com/2",
            content_hash="hash2",
            topic_tags=["renewables_wind"],
        )
        db.add_all([article1, article2])
        await db.flush()
        
        # Create chunks
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["solar energy", "wind energy"])
        
        chunk1 = ArticleChunk(
            article_id=article1.id,
            chunk_index=0,
            text="Solar energy text",
            embedding=embeddings[0],
            topic_tags=["renewables_solar"],
        )
        chunk2 = ArticleChunk(
            article_id=article2.id,
            chunk_index=0,
            text="Wind energy text",
            embedding=embeddings[1],
            topic_tags=["renewables_wind"],
        )
        db.add_all([chunk1, chunk2])
        await db.commit()
        
        # Search with solar topic filter
        search_service = VectorSearchService(provider)
        filters = SearchFilters(topics=["renewables_solar"])
        results = await search_service.search(db, "energy", filters=filters, k=5)
        
        assert len(results) == 1
        assert results[0].article_title == "Solar article"


@pytest.mark.asyncio
async def test_search_with_date_filter(test_db):
    """Test search with date range filter."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        now = datetime.utcnow()
        past = now - timedelta(days=10)
        
        # Create articles with different dates
        article1 = Article(
            source_id=source.id,
            title="Recent",
            url="https://test.com/1",
            content_hash="hash1",
            published_at=now,
        )
        article2 = Article(
            source_id=source.id,
            title="Old",
            url="https://test.com/2",
            content_hash="hash2",
            published_at=past,
        )
        db.add_all([article1, article2])
        await db.flush()
        
        # Create chunks
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["recent news", "old news"])
        
        chunk1 = ArticleChunk(
            article_id=article1.id,
            chunk_index=0,
            text="Recent news",
            embedding=embeddings[0],
            published_at=now,
        )
        chunk2 = ArticleChunk(
            article_id=article2.id,
            chunk_index=0,
            text="Old news",
            embedding=embeddings[1],
            published_at=past,
        )
        db.add_all([chunk1, chunk2])
        await db.commit()
        
        # Search with date filter (last 5 days)
        search_service = VectorSearchService(provider)
        filters = SearchFilters(date_from=now - timedelta(days=5))
        results = await search_service.search(db, "news", filters=filters, k=5)
        
        assert len(results) == 1
        assert results[0].article_title == "Recent"


@pytest.mark.asyncio
async def test_search_similarity_order(test_db):
    """Test that results are ordered by similarity."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create articles
        articles = []
        for i in range(3):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/{i}",
                content_hash=f"hash{i}",
            )
            db.add(article)
            articles.append(article)
        await db.flush()
        
        # Create chunks with different texts
        provider = FakeEmbeddingProvider(dimension=1536)
        texts = [
            "solar energy is renewable",  # Most similar to query
            "wind power generation",
            "fossil fuel extraction",  # Least similar to query
        ]
        embeddings = await provider.embed(texts)
        
        for i, (article, text, embedding) in enumerate(zip(articles, texts, embeddings)):
            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=0,
                text=text,
                embedding=embedding,
            )
            db.add(chunk)
        await db.commit()
        
        # Search
        search_service = VectorSearchService(provider)
        results = await search_service.search(db, "solar energy is renewable", k=3)
        
        assert len(results) == 3
        
        # First result should have highest similarity
        assert results[0].similarity >= results[1].similarity
        assert results[1].similarity >= results[2].similarity
        
        # First result should be most similar text
        assert results[0].chunk_text == "solar energy is renewable"


@pytest.mark.asyncio
async def test_search_limit_k(test_db):
    """Test that search respects k limit."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create 10 articles with chunks
        provider = FakeEmbeddingProvider(dimension=1536)
        
        for i in range(10):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/{i}",
                content_hash=f"hash{i}",
            )
            db.add(article)
            await db.flush()
            
            embeddings = await provider.embed([f"text {i}"])
            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=0,
                text=f"text {i}",
                embedding=embeddings[0],
            )
            db.add(chunk)
        
        await db.commit()
        
        # Search with k=3
        search_service = VectorSearchService(provider)
        results = await search_service.search(db, "text", k=3)
        
        assert len(results) == 3


@pytest.mark.asyncio
async def test_search_with_threshold(test_db):
    """Test search with similarity threshold."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Test",
            url="https://test.com/1",
            content_hash="hash1",
        )
        db.add(article)
        await db.flush()
        
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["completely different topic"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="completely different topic",
            embedding=embeddings[0],
        )
        db.add(chunk)
        await db.commit()
        
        # Search with high similarity threshold
        search_service = VectorSearchService(provider)
        results = await search_service.search_with_threshold(
            db, "solar energy", min_similarity=0.9, k=5
        )
        
        # Should filter out low similarity results
        assert len(results) == 0


@pytest.mark.asyncio
async def test_search_result_to_dict(test_db):
    """Test SearchResult to_dict conversion."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Test Article",
            url="https://test.com/article",
            content_hash="hash1",
            published_at=datetime(2026, 1, 20),
            country_codes=["US", "UK"],
            topic_tags=["renewables_solar"],
        )
        db.add(article)
        await db.flush()
        
        provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await provider.embed(["test content"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="test content",
            embedding=embeddings[0],
            country_codes=["US", "UK"],
            topic_tags=["renewables_solar"],
            published_at=article.published_at,
        )
        db.add(chunk)
        await db.commit()
        
        # Search
        search_service = VectorSearchService(provider)
        results = await search_service.search(db, "test", k=1)
        
        assert len(results) == 1
        result_dict = results[0].to_dict()
        
        # Verify structure
        assert "chunk_id" in result_dict
        assert "chunk_text" in result_dict
        assert "similarity" in result_dict
        assert "article" in result_dict
        assert result_dict["article"]["title"] == "Test Article"
        assert result_dict["article"]["country_codes"] == ["US", "UK"]
        assert result_dict["article"]["topic_tags"] == ["renewables_solar"]


@pytest.mark.asyncio
async def test_search_multiple_chunks_same_article(test_db):
    """Test search can return multiple chunks from same article."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Long Article",
            url="https://test.com/long",
            content_hash="hash1",
        )
        db.add(article)
        await db.flush()
        
        # Create multiple chunks for same article
        provider = FakeEmbeddingProvider(dimension=1536)
        texts = ["solar energy part 1", "solar energy part 2", "solar energy part 3"]
        embeddings = await provider.embed(texts)
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=i,
                text=text,
                embedding=embedding,
            )
            db.add(chunk)
        await db.commit()
        
        # Search
        search_service = VectorSearchService(provider)
        results = await search_service.search(db, "solar energy", k=5)
        
        # Should return all chunks
        assert len(results) == 3
        
        # All from same article
        assert all(r.article_id == article.id for r in results)
        
        # Different chunk indices
        chunk_indices = [r.chunk_index for r in results]
        assert len(set(chunk_indices)) == 3

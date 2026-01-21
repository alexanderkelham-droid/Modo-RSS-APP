"""
Tests for RAG chat service.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.db.models import Article, ArticleChunk, Source
from app.services.rag.chat_service import ChatService, SearchFilters
from app.services.rag.embedding_provider import FakeEmbeddingProvider
from app.services.rag.chat_provider import FakeChatProvider


@pytest.mark.asyncio
async def test_chat_basic(test_db):
    """Test basic chat functionality."""
    async with test_db() as db:
        # Create test data
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Solar Energy Breakthrough",
            url="https://test.com/solar",
            content_hash="hash1",
            published_at=datetime.utcnow(),
            country_codes=["US"],
            topic_tags=["renewables_solar"],
        )
        db.add(article)
        await db.flush()
        
        # Create chunk with embedding
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await embedding_provider.embed(["Solar panels are becoming more efficient"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="Solar panels are becoming more efficient and cost-effective.",
            embedding=embeddings[0],
            country_codes=["US"],
            topic_tags=["renewables_solar"],
            published_at=article.published_at,
        )
        db.add(chunk)
        await db.commit()
        
        # Create chat service
        chat_provider = FakeChatProvider(predefined_response="Solar panels are improving [1].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        # Ask question
        response = await chat_service.chat(
            db=db,
            question="How are solar panels improving?",
            k=5,
        )
        
        assert response.answer == "Solar panels are improving [1]."
        assert len(response.citations) == 1
        assert response.citations[0].title == "Solar Energy Breakthrough"
        assert response.confidence in ["high", "medium", "low"]


@pytest.mark.asyncio
async def test_chat_no_results(test_db):
    """Test chat when no relevant results found."""
    async with test_db() as db:
        # No data in database
        
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        chat_provider = FakeChatProvider()
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        response = await chat_service.chat(
            db=db,
            question="What about solar energy?",
            k=5,
        )
        
        assert "don't have enough information" in response.answer
        assert len(response.citations) == 0
        assert response.confidence == "low"


@pytest.mark.asyncio
async def test_chat_with_country_filter(test_db):
    """Test chat with country filter."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # US article
        article1 = Article(
            source_id=source.id,
            title="US Solar",
            url="https://test.com/us",
            content_hash="hash1",
            country_codes=["US"],
        )
        # Germany article
        article2 = Article(
            source_id=source.id,
            title="Germany Solar",
            url="https://test.com/de",
            content_hash="hash2",
            country_codes=["DE"],
        )
        db.add_all([article1, article2])
        await db.flush()
        
        # Create chunks
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await embedding_provider.embed(["US solar", "Germany solar"])
        
        chunk1 = ArticleChunk(
            article_id=article1.id,
            chunk_index=0,
            text="US solar developments",
            embedding=embeddings[0],
            country_codes=["US"],
        )
        chunk2 = ArticleChunk(
            article_id=article2.id,
            chunk_index=0,
            text="Germany solar developments",
            embedding=embeddings[1],
            country_codes=["DE"],
        )
        db.add_all([chunk1, chunk2])
        await db.commit()
        
        # Chat with US filter
        chat_provider = FakeChatProvider(predefined_response="US solar answer [1].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        filters = SearchFilters(countries=["US"])
        response = await chat_service.chat(
            db=db,
            question="Solar developments?",
            filters=filters,
            k=5,
        )
        
        # Should only get US article
        assert len(response.citations) == 1
        assert response.citations[0].title == "US Solar"
        assert response.filters_applied["countries"] == ["US"]


@pytest.mark.asyncio
async def test_chat_with_topic_filter(test_db):
    """Test chat with topic filter."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Solar Article",
            url="https://test.com/solar",
            content_hash="hash1",
            topic_tags=["renewables_solar"],
        )
        db.add(article)
        await db.flush()
        
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await embedding_provider.embed(["solar text"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="Solar energy content",
            embedding=embeddings[0],
            topic_tags=["renewables_solar"],
        )
        db.add(chunk)
        await db.commit()
        
        # Chat with solar filter
        chat_provider = FakeChatProvider(predefined_response="Solar answer [1].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        filters = SearchFilters(topics=["renewables_solar"])
        response = await chat_service.chat(
            db=db,
            question="Solar?",
            filters=filters,
            k=5,
        )
        
        assert len(response.citations) >= 1
        assert response.filters_applied["topics"] == ["renewables_solar"]


@pytest.mark.asyncio
async def test_chat_confidence_assessment(test_db):
    """Test confidence assessment based on similarity."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Test Article",
            url="https://test.com/article",
            content_hash="hash1",
        )
        db.add(article)
        await db.flush()
        
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        # Create chunk with embedding that will have high similarity
        embeddings = await embedding_provider.embed(["exact match question text"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="exact match question text",
            embedding=embeddings[0],
        )
        db.add(chunk)
        await db.commit()
        
        chat_provider = FakeChatProvider(predefined_response="Answer [1].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        # Ask exact matching question
        response = await chat_service.chat(
            db=db,
            question="exact match question text",
            k=5,
        )
        
        # Should have high confidence due to high similarity
        assert response.confidence in ["high", "medium"]


@pytest.mark.asyncio
async def test_chat_multiple_citations(test_db):
    """Test chat with multiple source articles."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Create multiple articles
        articles = []
        for i in range(3):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/article{i}",
                content_hash=f"hash{i}",
            )
            db.add(article)
            articles.append(article)
        await db.flush()
        
        # Create chunks
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        texts = [f"content {i}" for i in range(3)]
        embeddings = await embedding_provider.embed(texts)
        
        for i, (article, text, embedding) in enumerate(zip(articles, texts, embeddings)):
            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=0,
                text=text,
                embedding=embedding,
            )
            db.add(chunk)
        await db.commit()
        
        chat_provider = FakeChatProvider(predefined_response="Answer with citations [1][2][3].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        response = await chat_service.chat(
            db=db,
            question="content",
            k=5,
        )
        
        # Should have multiple citations
        assert len(response.citations) == 3


@pytest.mark.asyncio
async def test_chat_deduplicates_citations(test_db):
    """Test that citations are deduplicated by article."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Article",
            url="https://test.com/article",
            content_hash="hash1",
        )
        db.add(article)
        await db.flush()
        
        # Create multiple chunks from same article
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        texts = ["chunk 1", "chunk 2", "chunk 3"]
        embeddings = await embedding_provider.embed(texts)
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=i,
                text=text,
                embedding=embedding,
            )
            db.add(chunk)
        await db.commit()
        
        chat_provider = FakeChatProvider(predefined_response="Answer [1].")
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        response = await chat_service.chat(
            db=db,
            question="chunk",
            k=5,
        )
        
        # Should only have 1 citation despite 3 chunks
        assert len(response.citations) == 1


@pytest.mark.asyncio
async def test_chat_system_prompt_includes_context(test_db):
    """Test that system prompt includes chunk context."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Test",
            url="https://test.com/test",
            content_hash="hash1",
            published_at=datetime(2026, 1, 15),
        )
        db.add(article)
        await db.flush()
        
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await embedding_provider.embed(["specific content here"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="specific content here",
            embedding=embeddings[0],
            published_at=article.published_at,
        )
        db.add(chunk)
        await db.commit()
        
        chat_provider = FakeChatProvider()  # Will check for context
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
        )
        
        response = await chat_service.chat(
            db=db,
            question="specific content",
            k=5,
        )
        
        # FakeChatProvider should detect context and generate answer
        assert "don't have enough information in the ingested corpus" not in response.answer


@pytest.mark.asyncio
async def test_chat_low_similarity_threshold(test_db):
    """Test chat rejects results below similarity threshold."""
    async with test_db() as db:
        source = Source(name="Test", url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        article = Article(
            source_id=source.id,
            title="Unrelated",
            url="https://test.com/unrelated",
            content_hash="hash1",
        )
        db.add(article)
        await db.flush()
        
        embedding_provider = FakeEmbeddingProvider(dimension=1536)
        embeddings = await embedding_provider.embed(["completely different topic"])
        
        chunk = ArticleChunk(
            article_id=article.id,
            chunk_index=0,
            text="completely different topic",
            embedding=embeddings[0],
        )
        db.add(chunk)
        await db.commit()
        
        chat_provider = FakeChatProvider()
        chat_service = ChatService(
            embedding_provider=embedding_provider,
            chat_provider=chat_provider,
            min_similarity_threshold=0.9,  # Very high threshold
        )
        
        response = await chat_service.chat(
            db=db,
            question="solar energy",
            k=5,
        )
        
        # Should reject due to low similarity
        assert "don't have enough information" in response.answer
        assert response.confidence == "low"

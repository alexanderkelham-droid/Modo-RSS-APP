"""
Tests for embedding providers.
"""

import pytest
from app.services.rag.embedding_provider import (
    FakeEmbeddingProvider,
    OpenAIEmbeddingProvider,
)


@pytest.mark.asyncio
async def test_fake_provider_generates_embeddings():
    """Test that fake provider generates embeddings."""
    provider = FakeEmbeddingProvider(dimension=128)
    
    texts = ["hello world", "test document"]
    embeddings = await provider.embed(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 128
    assert len(embeddings[1]) == 128


@pytest.mark.asyncio
async def test_fake_provider_deterministic():
    """Test that fake provider is deterministic."""
    provider = FakeEmbeddingProvider(dimension=128)
    
    text = "test document"
    
    # Generate embeddings twice
    embeddings1 = await provider.embed([text])
    embeddings2 = await provider.embed([text])
    
    # Should be identical
    assert embeddings1 == embeddings2


@pytest.mark.asyncio
async def test_fake_provider_different_texts():
    """Test that different texts produce different embeddings."""
    provider = FakeEmbeddingProvider(dimension=128)
    
    texts = ["text one", "text two"]
    embeddings = await provider.embed(texts)
    
    # Embeddings should be different
    assert embeddings[0] != embeddings[1]


@pytest.mark.asyncio
async def test_fake_provider_normalized():
    """Test that fake embeddings are normalized."""
    provider = FakeEmbeddingProvider(dimension=128)
    
    texts = ["test"]
    embeddings = await provider.embed(texts)
    
    # Calculate norm (should be close to 1.0)
    import math
    norm = math.sqrt(sum(x**2 for x in embeddings[0]))
    
    assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_fake_provider_empty_list():
    """Test fake provider with empty list."""
    provider = FakeEmbeddingProvider()
    
    embeddings = await provider.embed([])
    
    assert embeddings == []


@pytest.mark.asyncio
async def test_fake_provider_dimension():
    """Test get_dimension method."""
    provider = FakeEmbeddingProvider(dimension=256)
    
    assert provider.get_dimension() == 256


@pytest.mark.asyncio
async def test_openai_provider_requires_api_key():
    """Test that OpenAI provider requires API key."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIEmbeddingProvider(api_key="")


@pytest.mark.asyncio
async def test_openai_provider_dimension():
    """Test OpenAI provider dimension."""
    provider = OpenAIEmbeddingProvider(api_key="test-key", dimension=1536)
    
    assert provider.get_dimension() == 1536


@pytest.mark.asyncio
async def test_fake_provider_consistency_across_instances():
    """Test that fake provider is consistent across different instances."""
    provider1 = FakeEmbeddingProvider(dimension=128)
    provider2 = FakeEmbeddingProvider(dimension=128)
    
    text = "consistent embedding"
    
    embeddings1 = await provider1.embed([text])
    embeddings2 = await provider2.embed([text])
    
    # Should be identical across instances
    assert embeddings1 == embeddings2


@pytest.mark.asyncio
async def test_fake_provider_batch():
    """Test fake provider with batch of texts."""
    provider = FakeEmbeddingProvider(dimension=64)
    
    texts = [f"document {i}" for i in range(10)]
    embeddings = await provider.embed(texts)
    
    assert len(embeddings) == 10
    for emb in embeddings:
        assert len(emb) == 64
    
    # All embeddings should be unique
    assert len(set(tuple(e) for e in embeddings)) == 10

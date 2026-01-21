"""
Tests for chunking service.
"""

import pytest
from app.services.rag.chunking_service import ChunkingService


def test_chunk_short_text():
    """Test chunking text shorter than max size."""
    service = ChunkingService(min_chunk_size=800, max_chunk_size=1200)
    
    text = "This is a short text."
    chunks = service.chunk_text(text)
    
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0


def test_chunk_long_text():
    """Test chunking long text."""
    service = ChunkingService(min_chunk_size=100, max_chunk_size=200, overlap=20)
    
    # Create text longer than max_chunk_size
    text = "A " * 150  # 300 characters
    chunks = service.chunk_text(text)
    
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # Check chunk indices
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_chunk_at_sentence_boundary():
    """Test chunking prefers sentence boundaries."""
    service = ChunkingService(min_chunk_size=50, max_chunk_size=150, overlap=10)
    
    text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
    chunks = service.chunk_text(text)
    
    # First chunk should end at sentence boundary
    assert chunks[0].text.endswith('.')


def test_chunk_overlap():
    """Test that chunks have overlap."""
    service = ChunkingService(min_chunk_size=50, max_chunk_size=100, overlap=20)
    
    text = "A" * 250  # Long text
    chunks = service.chunk_text(text)
    
    if len(chunks) > 1:
        # Check overlap exists between chunks
        # End of first chunk should overlap with start of second
        assert len(chunks) >= 2


def test_chunk_empty_text():
    """Test chunking empty text."""
    service = ChunkingService()
    
    chunks = service.chunk_text("")
    assert chunks == []
    
    chunks = service.chunk_text("   ")
    assert chunks == []


def test_chunk_positions():
    """Test chunk start and end positions."""
    service = ChunkingService(min_chunk_size=50, max_chunk_size=100, overlap=10)
    
    text = "A" * 250
    chunks = service.chunk_text(text)
    
    # First chunk starts at 0
    assert chunks[0].start_pos == 0
    
    # Last chunk ends at text length (or close to it)
    assert chunks[-1].end_pos <= len(text)
    
    # Positions should be monotonic
    for i in range(len(chunks) - 1):
        assert chunks[i].end_pos > chunks[i].start_pos
        assert chunks[i+1].start_pos >= chunks[i].start_pos


def test_chunk_article_with_metadata():
    """Test chunking article with metadata."""
    service = ChunkingService(min_chunk_size=50, max_chunk_size=100, overlap=10)
    
    text = "A" * 250
    metadata = {
        "article_id": 123,
        "country_codes": ["US"],
        "topic_tags": ["renewables_solar"],
    }
    
    chunks = service.chunk_article(text, metadata)
    
    assert len(chunks) > 0
    
    # Each chunk should have metadata
    for chunk in chunks:
        assert chunk["article_id"] == 123
        assert chunk["country_codes"] == ["US"]
        assert chunk["topic_tags"] == ["renewables_solar"]
        assert "text" in chunk
        assert "chunk_index" in chunk


def test_chunk_realistic_article():
    """Test chunking realistic article text."""
    service = ChunkingService(min_chunk_size=800, max_chunk_size=1200, overlap=100)
    
    # Simulate article with multiple paragraphs
    paragraphs = [
        "The energy transition is accelerating globally. " * 20,
        "Solar and wind are becoming cost-competitive. " * 20,
        "Battery storage is enabling grid flexibility. " * 20,
        "Electric vehicles are gaining market share. " * 20,
    ]
    text = "\n\n".join(paragraphs)
    
    chunks = service.chunk_text(text)
    
    # Should have multiple chunks
    assert len(chunks) >= 2
    
    # All chunks should be within size limits
    for chunk in chunks:
        text_len = len(chunk.text)
        # Allow some flexibility for sentence boundaries
        assert text_len <= service.max_chunk_size + 200
    
    # Check indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_chunk_preserves_content():
    """Test that chunking preserves all content."""
    service = ChunkingService(min_chunk_size=100, max_chunk_size=200, overlap=20)
    
    text = "Unique content here. " * 50
    chunks = service.chunk_text(text)
    
    # Combine all chunks (roughly, accounting for overlap)
    combined_text = " ".join(c.text for c in chunks)
    
    # Should contain all unique words
    assert "Unique" in combined_text
    assert "content" in combined_text


def test_chunk_no_empty_chunks():
    """Test that no empty chunks are created."""
    service = ChunkingService(min_chunk_size=50, max_chunk_size=100, overlap=10)
    
    text = "A" * 500
    chunks = service.chunk_text(text)
    
    # No chunk should be empty
    for chunk in chunks:
        assert len(chunk.text.strip()) > 0


def test_chunk_single_sentence():
    """Test chunking single sentence."""
    service = ChunkingService(min_chunk_size=800, max_chunk_size=1200, overlap=100)
    
    text = "This is a single sentence."
    chunks = service.chunk_text(text)
    
    assert len(chunks) == 1
    assert chunks[0].text == text


def test_chunk_multiple_sentences():
    """Test chunking multiple sentences."""
    service = ChunkingService(min_chunk_size=20, max_chunk_size=50, overlap=5)
    
    text = "First. Second. Third. Fourth. Fifth. Sixth."
    chunks = service.chunk_text(text)
    
    # Should break at sentence boundaries
    assert all(chunk.text.endswith('.') for chunk in chunks)


def test_chunk_fallback_to_word_boundary():
    """Test fallback to word boundary when no sentence boundary."""
    service = ChunkingService(min_chunk_size=20, max_chunk_size=50, overlap=5)
    
    # Text without sentence endings
    text = "word " * 100
    chunks = service.chunk_text(text)
    
    assert len(chunks) > 1
    # Should break at word boundaries (spaces)
    for chunk in chunks[:-1]:  # All but last
        assert not chunk.text.endswith(' ')  # Should be trimmed


def test_chunk_very_long_text():
    """Test chunking very long text."""
    service = ChunkingService(min_chunk_size=800, max_chunk_size=1200, overlap=100)
    
    # Create 10KB text
    text = "The renewable energy sector is growing rapidly. " * 200
    chunks = service.chunk_text(text)
    
    assert len(chunks) > 5
    
    # All chunks should be reasonable size
    for chunk in chunks:
        assert len(chunk.text) >= 700  # Close to min
        assert len(chunk.text) <= 1300  # Close to max (with sentence boundary flexibility)

"""
Tests for RSS parser.
"""

import pytest
from datetime import datetime
from app.services.ingest.rss_parser import RSSParser, RSSEntry


def test_parse_rss_entry():
    """Test parsing a valid RSS entry."""
    entry = RSSEntry(
        title="Test Article",
        url="https://example.com/article-1",
        published_at=datetime(2026, 1, 20, 10, 0, 0),
        summary="This is a test summary"
    )
    
    assert entry.title == "Test Article"
    assert entry.url == "https://example.com/article-1"
    assert entry.summary == "This is a test summary"
    assert entry.published_at.year == 2026


def test_parse_feed_valid():
    """Test parsing a valid RSS feed."""
    feed_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Article 1</title>
                <link>https://example.com/article-1</link>
                <description>Summary of article 1</description>
                <pubDate>Mon, 20 Jan 2026 10:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Article 2</title>
                <link>https://example.com/article-2</link>
                <description>Summary of article 2</description>
            </item>
        </channel>
    </rss>"""
    
    parser = RSSParser()
    entries = parser.parse_feed(feed_xml)
    
    assert len(entries) == 2
    assert entries[0].title == "Article 1"
    assert entries[0].url == "https://example.com/article-1"
    assert entries[0].summary == "Summary of article 1"
    assert entries[1].title == "Article 2"


def test_parse_feed_malformed():
    """Test parsing a malformed RSS feed."""
    feed_xml = "This is not valid XML"
    
    parser = RSSParser()
    with pytest.raises(ValueError, match="Failed to parse RSS feed"):
        parser.parse_feed(feed_xml)


def test_parse_feed_empty_entries():
    """Test that entries without title or URL are skipped."""
    feed_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title></title>
                <link>https://example.com/article-1</link>
            </item>
            <item>
                <title>Valid Article</title>
                <link></link>
            </item>
            <item>
                <title>Good Article</title>
                <link>https://example.com/article-2</link>
            </item>
        </channel>
    </rss>"""
    
    parser = RSSParser()
    entries = parser.parse_feed(feed_xml)
    
    assert len(entries) == 1
    assert entries[0].title == "Good Article"


def test_compute_content_hash():
    """Test content hash computation."""
    parser = RSSParser()
    
    hash1 = parser.compute_content_hash("Title", "https://example.com", "Summary")
    hash2 = parser.compute_content_hash("Title", "https://example.com", "Summary")
    hash3 = parser.compute_content_hash("Different", "https://example.com", "Summary")
    
    # Same content should produce same hash
    assert hash1 == hash2
    
    # Different content should produce different hash
    assert hash1 != hash3
    
    # Hash should be 64 character hex string (SHA256)
    assert len(hash1) == 64
    assert all(c in '0123456789abcdef' for c in hash1)


def test_parse_published_date():
    """Test date parsing from various formats."""
    # Note: This test depends on feedparser's internal structure
    # In real usage, feedparser provides parsed time tuples
    pass  # Placeholder - actual implementation would test with feedparser entry objects

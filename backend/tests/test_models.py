"""
Tests for database models.
"""

import pytest
from datetime import datetime
from app.db.models import Source, Article, IngestionRun


def test_source_model():
    """Test Source model instantiation."""
    source = Source(
        name="Test Source",
        type="rss",
        rss_url="https://example.com/feed.xml",
        enabled=True
    )
    
    assert source.name == "Test Source"
    assert source.type == "rss"
    assert source.enabled is True
    assert source.rss_url == "https://example.com/feed.xml"


def test_article_model():
    """Test Article model instantiation."""
    article = Article(
        source_id=1,
        title="Test Article",
        url="https://example.com/article-1",
        published_at=datetime.utcnow(),
        raw_summary="This is a summary",
        content_text="Full article content here",
        language="en",
        country_codes=["US", "GB"],
        topic_tags=["renewables_solar", "policy_regulation"]
    )
    
    assert article.title == "Test Article"
    assert article.source_id == 1
    assert "US" in article.country_codes
    assert "renewables_solar" in article.topic_tags


def test_ingestion_run_model():
    """Test IngestionRun model instantiation."""
    run = IngestionRun(
        status="running",
        stats={"new": 10, "updated": 5, "failed": 2}
    )
    
    assert run.status == "running"
    assert run.stats["new"] == 10
    assert run.stats["updated"] == 5

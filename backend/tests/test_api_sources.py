"""
Integration tests for sources CRUD API.
"""

import pytest
from httpx import AsyncClient

from app.db.models import Source, Article


@pytest.mark.asyncio
async def test_list_sources_empty(test_db, async_client: AsyncClient):
    """Test listing sources when none exist."""
    response = await async_client.get("/sources")
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_sources_basic(test_db, async_client: AsyncClient):
    """Test basic source listing."""
    async with test_db() as db:
        source1 = Source(name="Source A", rss_url="https://a.com/rss", enabled=True)
        source2 = Source(name="Source B", rss_url="https://b.com/rss", enabled=False)
        db.add_all([source1, source2])
        await db.commit()
    
    response = await async_client.get("/sources")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    
    # Check ordering (alphabetical by name)
    assert data["items"][0]["name"] == "Source A"
    assert data["items"][1]["name"] == "Source B"


@pytest.mark.asyncio
async def test_list_sources_enabled_filter(test_db, async_client: AsyncClient):
    """Test filtering sources by enabled status."""
    async with test_db() as db:
        source1 = Source(name="Enabled", rss_url="https://enabled.com/rss", enabled=True)
        source2 = Source(name="Disabled", rss_url="https://disabled.com/rss", enabled=False)
        db.add_all([source1, source2])
        await db.commit()
    
    # Filter enabled
    response = await async_client.get("/sources?enabled=true")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Enabled"
    
    # Filter disabled
    response = await async_client.get("/sources?enabled=false")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Disabled"


@pytest.mark.asyncio
async def test_list_sources_with_article_counts(test_db, async_client: AsyncClient):
    """Test that source listing includes article counts."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        
        # Add articles
        for i in range(3):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://test.com/{i}",
                content_hash=f"hash{i}",
            )
            db.add(article)
        await db.commit()
    
    response = await async_client.get("/sources")
    
    data = response.json()
    assert data["items"][0]["article_count"] == 3


@pytest.mark.asyncio
async def test_get_source(test_db, async_client: AsyncClient):
    """Test getting a specific source."""
    async with test_db() as db:
        source = Source(name="Test Source", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        source_id = source.id
        await db.commit()
    
    response = await async_client.get(f"/sources/{source_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Source"
    assert data["rss_url"] == "https://test.com/rss"
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_get_source_not_found(test_db, async_client: AsyncClient):
    """Test getting non-existent source."""
    response = await async_client.get("/sources/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_source(test_db, async_client: AsyncClient):
    """Test creating a new source."""
    source_data = {
        "name": "New Source",
        "rss_url": "https://newsource.com/rss",
        "enabled": True,
        "type": "rss",
    }
    
    response = await async_client.post("/sources", json=source_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Source"
    assert data["rss_url"] == "https://newsource.com/rss"
    assert data["enabled"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_source_duplicate_name(test_db, async_client: AsyncClient):
    """Test creating source with duplicate name fails."""
    async with test_db() as db:
        source = Source(name="Existing", rss_url="https://existing.com/rss", enabled=True)
        db.add(source)
        await db.commit()
    
    source_data = {
        "name": "Existing",
        "rss_url": "https://different.com/rss",
        "enabled": True,
    }
    
    response = await async_client.post("/sources", json=source_data)
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_source(test_db, async_client: AsyncClient):
    """Test updating a source."""
    async with test_db() as db:
        source = Source(name="Original", rss_url="https://original.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        source_id = source.id
        await db.commit()
    
    update_data = {
        "name": "Updated",
        "enabled": False,
    }
    
    response = await async_client.put(f"/sources/{source_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["enabled"] is False
    # RSS URL should remain unchanged
    assert data["rss_url"] == "https://original.com/rss"


@pytest.mark.asyncio
async def test_update_source_enable_disable(test_db, async_client: AsyncClient):
    """Test enabling/disabling a source."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        source_id = source.id
        await db.commit()
    
    # Disable
    response = await async_client.put(f"/sources/{source_id}", json={"enabled": False})
    assert response.json()["enabled"] is False
    
    # Enable
    response = await async_client.put(f"/sources/{source_id}", json={"enabled": True})
    assert response.json()["enabled"] is True


@pytest.mark.asyncio
async def test_update_source_not_found(test_db, async_client: AsyncClient):
    """Test updating non-existent source."""
    response = await async_client.put("/sources/99999", json={"name": "Test"})
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_source_duplicate_name(test_db, async_client: AsyncClient):
    """Test updating source to duplicate name fails."""
    async with test_db() as db:
        source1 = Source(name="Source 1", rss_url="https://1.com/rss", enabled=True)
        source2 = Source(name="Source 2", rss_url="https://2.com/rss", enabled=True)
        db.add_all([source1, source2])
        await db.flush()
        source2_id = source2.id
        await db.commit()
    
    response = await async_client.put(f"/sources/{source2_id}", json={"name": "Source 1"})
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_source(test_db, async_client: AsyncClient):
    """Test deleting a source."""
    async with test_db() as db:
        source = Source(name="To Delete", rss_url="https://delete.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        source_id = source.id
        await db.commit()
    
    response = await async_client.delete(f"/sources/{source_id}")
    
    assert response.status_code == 204
    
    # Verify deleted
    response = await async_client.get(f"/sources/{source_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_not_found(test_db, async_client: AsyncClient):
    """Test deleting non-existent source."""
    response = await async_client.delete("/sources/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_cascades_articles(test_db, async_client: AsyncClient):
    """Test that deleting source also deletes its articles."""
    async with test_db() as db:
        source = Source(name="Test", rss_url="https://test.com/rss", enabled=True)
        db.add(source)
        await db.flush()
        source_id = source.id
        
        # Add article
        article = Article(
            source_id=source.id,
            title="Test",
            url="https://test.com/article",
            content_hash="hash1",
        )
        db.add(article)
        await db.commit()
    
    # Delete source
    response = await async_client.delete(f"/sources/{source_id}")
    assert response.status_code == 204
    
    # Verify articles are also deleted
    async with test_db() as db:
        from sqlalchemy import select
        result = await db.execute(select(Article))
        articles = result.scalars().all()
        assert len(articles) == 0

"""
API endpoints for source CRUD operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.db.session import get_db
from app.db.models import Source, Article
from app.models.sources import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=SourceListResponse)
async def list_sources(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all RSS sources.
    
    Optional filters:
    - enabled: Filter by enabled/disabled status
    """
    # Build query
    query = select(Source)
    
    if enabled is not None:
        query = query.where(Source.enabled == enabled)
    
    query = query.order_by(Source.name)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    # Get article counts for each source
    items = []
    for source in sources:
        # Count articles for this source
        count_query = select(func.count()).select_from(Article).where(
            Article.source_id == source.id
        )
        count_result = await db.execute(count_query)
        article_count = count_result.scalar() or 0
        
        items.append(SourceResponse(
            id=source.id,
            name=source.name,
            rss_url=source.rss_url,
            enabled=source.enabled,
            type=source.type,
            created_at=source.created_at,
            article_count=article_count,
        ))
    
    return SourceListResponse(
        items=items,
        total=len(items),
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific source by ID."""
    query = select(Source).where(Source.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Get article count
    count_query = select(func.count()).select_from(Article).where(
        Article.source_id == source.id
    )
    count_result = await db.execute(count_query)
    article_count = count_result.scalar() or 0
    
    return SourceResponse(
        id=source.id,
        name=source.name,
        rss_url=source.rss_url,
        enabled=source.enabled,
        type=source.type,
        created_at=source.created_at,
        article_count=article_count,
    )


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    source: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new RSS source.
    
    The source will be automatically enabled unless specified otherwise.
    """
    # Check if name already exists
    existing_query = select(Source).where(Source.name == source.name)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source name already exists")
    
    # Create source
    new_source = Source(
        name=source.name,
        rss_url=source.rss_url,
        enabled=source.enabled,
        type=source.type,
    )
    
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    return SourceResponse(
        id=new_source.id,
        name=new_source.name,
        rss_url=new_source.rss_url,
        enabled=new_source.enabled,
        type=new_source.type,
        created_at=new_source.created_at,
        article_count=0,
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_update: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a source.
    
    All fields are optional. Only provided fields will be updated.
    Use this endpoint to enable/disable sources.
    """
    # Get existing source
    query = select(Source).where(Source.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update fields
    if source_update.name is not None:
        # Check name uniqueness
        existing_query = select(Source).where(
            Source.name == source_update.name,
            Source.id != source_id,
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Source name already exists")
        source.name = source_update.name
    
    if source_update.rss_url is not None:
        source.rss_url = source_update.rss_url
    
    if source_update.enabled is not None:
        source.enabled = source_update.enabled
    
    if source_update.type is not None:
        source.type = source_update.type
    
    await db.commit()
    await db.refresh(source)
    
    # Get article count
    count_query = select(func.count()).select_from(Article).where(
        Article.source_id == source.id
    )
    count_result = await db.execute(count_query)
    article_count = count_result.scalar() or 0
    
    return SourceResponse(
        id=source.id,
        name=source.name,
        rss_url=source.rss_url,
        enabled=source.enabled,
        type=source.type,
        created_at=source.created_at,
        article_count=article_count,
    )


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a source.
    
    Warning: This will also delete all articles from this source due to cascade delete.
    """
    # Check if source exists
    query = select(Source).where(Source.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Delete source (cascade will delete articles)
    await db.delete(source)
    await db.commit()
    
    return None

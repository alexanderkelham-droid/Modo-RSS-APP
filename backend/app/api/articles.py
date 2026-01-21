"""
API endpoints for articles listing and filtering.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, any_
from sqlalchemy.sql import text

from app.db.session import get_db
from app.db.models import Article, Source
from app.models.articles import (
    ArticleListResponse,
    ArticleListItem,
    TopStoriesResponse,
    TopStoryResponse,
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    country: Optional[str] = Query(None, description="ISO-3166 alpha-2 country code"),
    topic: Optional[str] = Query(None, description="Topic ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List articles with optional filters.
    
    Filters:
    - country: Filter by country code (e.g., 'GB', 'US')
    - topic: Filter by topic ID (e.g., 'renewables_solar')
    - days: Look back period (default 7 days)
    
    Pagination:
    - page: Page number (1-indexed)
    - page_size: Items per page (max 100)
    """
    # Build base query
    query = select(
        Article.id,
        Article.title,
        Article.url,
        Article.published_at,
        Article.country_codes,
        Article.topic_tags,
        Article.content_text,
        Source.name.label("source_name"),
    ).join(
        Source, Article.source_id == Source.id
    )
    
    # Apply filters
    filters = []
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    filters.append(Article.published_at >= cutoff_date)
    
    # Country filter
    if country:
        filters.append(country == any_(Article.country_codes))
    
    # Topic filter
    if topic:
        filters.append(topic == any_(Article.topic_tags))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by published date (newest first)
    query = query.order_by(desc(Article.published_at))
    
    # Count total
    count_query = select(func.count()).select_from(Article).join(Source)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Build response items
    items = []
    for row in rows:
        # Extract summary (first 200 chars)
        summary = None
        if row.content_text:
            summary = row.content_text[:200] + "..." if len(row.content_text) > 200 else row.content_text
        
        items.append(ArticleListItem(
            id=row.id,
            title=row.title,
            url=row.url,
            published_at=row.published_at,
            source_name=row.source_name,
            country_codes=row.country_codes,
            topic_tags=row.topic_tags,
            summary=summary,
        ))
    
    # Calculate pagination metadata
    has_next = (page * page_size) < total
    has_prev = page > 1
    
    return ArticleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )


@router.get("/top-stories", response_model=TopStoriesResponse)
async def get_top_stories(
    country: str = Query(..., description="ISO-3166 alpha-2 country code"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of stories to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top stories for a country using ranking heuristic.
    
    Ranking criteria (MVP heuristic):
    1. Recency (newer = higher score)
    2. Source reliability tier (tier 1 > tier 2 > tier 3)
    3. Keyword matching ("announcement", "policy", "breakthrough", etc.)
    
    Returns top N stories ordered by score.
    """
    # Build query
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(
        Article.id,
        Article.title,
        Article.url,
        Article.published_at,
        Article.country_codes,
        Article.topic_tags,
        Article.content_text,
        Source.name.label("source_name"),
    ).join(
        Source, Article.source_id == Source.id
    ).where(
        and_(
            country == any_(Article.country_codes),
            Article.published_at >= cutoff_date,
        )
    )
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Score each article
    now = datetime.utcnow()
    scored_articles = []
    
    # Keywords for boosting
    priority_keywords = [
        "announcement", "announced", "announce",
        "policy", "regulation", "law",
        "breakthrough", "innovation",
        "investment", "funding",
        "target", "goal", "commitment",
    ]
    
    # Source reliability tiers (MVP: heuristic based on domain)
    tier1_domains = ["reuters.com", "bloomberg.com", "ft.com", "wsj.com"]
    tier2_domains = ["theguardian.com", "bbc.com", "cnn.com"]
    # tier3 = everything else
    
    for row in rows:
        score = 0.0
        
        # 1. Recency score (0-40 points)
        if row.published_at:
            age_hours = (now - row.published_at).total_seconds() / 3600
            max_age_hours = days * 24
            recency_score = 40 * (1 - min(age_hours / max_age_hours, 1))
            score += recency_score
        
        # 2. Source reliability (0-30 points)
        source_domain = row.url.split('/')[2] if '://' in row.url else ''
        if any(tier1 in source_domain for tier1 in tier1_domains):
            score += 30
        elif any(tier2 in source_domain for tier2 in tier2_domains):
            score += 20
        else:
            score += 10
        
        # 3. Keyword matching (0-30 points)
        title_lower = row.title.lower()
        content_lower = (row.content_text or "").lower()
        
        keyword_matches = 0
        for keyword in priority_keywords:
            if keyword in title_lower:
                keyword_matches += 2  # Title matches worth more
            elif keyword in content_lower:
                keyword_matches += 1
        
        keyword_score = min(keyword_matches * 3, 30)  # Cap at 30
        score += keyword_score
        
        # Extract summary
        summary = None
        if row.content_text:
            summary = row.content_text[:200] + "..." if len(row.content_text) > 200 else row.content_text
        
        scored_articles.append({
            "id": row.id,
            "title": row.title,
            "url": row.url,
            "published_at": row.published_at,
            "source_name": row.source_name,
            "country_codes": row.country_codes,
            "topic_tags": row.topic_tags,
            "summary": summary,
            "score": round(score, 2),
        })
    
    # Sort by score (descending) and limit
    scored_articles.sort(key=lambda x: x["score"], reverse=True)
    top_stories = scored_articles[:limit]
    
    # Build response
    items = [TopStoryResponse(**story) for story in top_stories]
    
    return TopStoriesResponse(
        items=items,
        country=country,
        days=days,
    )

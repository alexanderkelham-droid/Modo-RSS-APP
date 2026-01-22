"""
API endpoints for statistics and analytics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, List

from app.db import get_db
from app.db.models import Article

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/activity")
async def get_activity_stats(
    days: int = 7,
    country_code: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get article activity statistics over time.
    
    Returns daily article counts for the specified period.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build query
    query = select(
        func.date(Article.published_at).label('date'),
        func.count(Article.id).label('count')
    ).where(
        Article.published_at >= start_date,
        Article.published_at <= end_date
    )
    
    # Add country filter if specified
    if country_code:
        query = query.where(Article.country_codes.contains([country_code]))
    
    query = query.group_by(func.date(Article.published_at)).order_by(func.date(Article.published_at))
    
    result = await db.execute(query)
    daily_counts = result.all()
    
    # Format response
    activity_data = []
    for row in daily_counts:
        activity_data.append({
            "date": row.date.isoformat() if row.date else None,
            "count": row.count
        })
    
    return {
        "days": days,
        "country_code": country_code,
        "data": activity_data,
        "total": sum(item["count"] for item in activity_data)
    }


@router.get("/topic-breakdown")
async def get_topic_breakdown(
    days: int = 7,
    country_code: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get article counts by topic for the specified period.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build base query
    query = select(Article).where(
        Article.published_at >= start_date,
        Article.published_at <= end_date,
        Article.topic_tags.isnot(None)
    )
    
    # Add country filter if specified
    if country_code:
        query = query.where(Article.country_codes.contains([country_code]))
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    # Count topics
    topic_counts = {}
    for article in articles:
        if article.topic_tags:
            for tag in article.topic_tags:
                topic_counts[tag] = topic_counts.get(tag, 0) + 1
    
    # Sort by count and get top topics
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "days": days,
        "country_code": country_code,
        "topics": [
            {"topic": topic, "count": count}
            for topic, count in sorted_topics[:10]
        ],
        "total": len(articles)
    }

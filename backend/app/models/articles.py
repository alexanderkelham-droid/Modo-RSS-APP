"""
Pydantic models for article API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ArticleResponse(BaseModel):
    """Article response model."""
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    fetched_at: datetime
    source_id: int
    source_name: str
    raw_summary: Optional[str]
    content_text: Optional[str]
    language: Optional[str]
    country_codes: Optional[List[str]]
    topic_tags: Optional[List[str]]
    
    class Config:
        from_attributes = True


class ArticleListItem(BaseModel):
    """Simplified article for list views."""
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    source_name: str
    country_codes: Optional[List[str]]
    topic_tags: Optional[List[str]]
    summary: Optional[str] = Field(None, description="First 200 chars of content")
    
    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Paginated article list response."""
    items: List[ArticleListItem]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class TopStoryResponse(BaseModel):
    """Top story response with ranking metadata."""
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    source_name: str
    country_codes: Optional[List[str]]
    topic_tags: Optional[List[str]]
    summary: Optional[str]
    score: float = Field(..., description="Ranking score")
    
    class Config:
        from_attributes = True


class TopStoriesResponse(BaseModel):
    """Top stories list response."""
    items: List[TopStoryResponse]
    country: str
    days: int

"""
Pydantic models for source CRUD API.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class SourceBase(BaseModel):
    """Base source fields."""
    name: str = Field(..., min_length=1, max_length=255)
    rss_url: str = Field(..., description="RSS feed URL")
    enabled: bool = Field(True, description="Whether source is enabled for ingestion")
    type: str = Field("rss", description="Source type")


class SourceCreate(SourceBase):
    """Create source request."""
    pass


class SourceUpdate(BaseModel):
    """Update source request (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    rss_url: Optional[str] = None
    enabled: Optional[bool] = None
    type: Optional[str] = None


class SourceResponse(SourceBase):
    """Source response model."""
    id: int
    created_at: datetime
    article_count: Optional[int] = Field(None, description="Number of articles from this source")
    
    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """List of sources."""
    items: list[SourceResponse]
    total: int

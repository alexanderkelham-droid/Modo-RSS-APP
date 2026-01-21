"""
Pydantic models for chat API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ChatFilters(BaseModel):
    """Filters for chat search."""
    countries: Optional[List[str]] = Field(None, description="ISO-3166 alpha-2 country codes")
    topics: Optional[List[str]] = Field(None, description="Topic IDs")
    date_from: Optional[datetime] = Field(None, description="Start date (inclusive)")
    date_to: Optional[datetime] = Field(None, description="End date (inclusive)")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    question: str = Field(..., description="User question", min_length=1)
    filters: Optional[ChatFilters] = Field(None, description="Optional search filters")
    k: Optional[int] = Field(8, description="Number of chunks to retrieve", ge=1, le=20)


class CitationResponse(BaseModel):
    """Citation in chat response."""
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    source: str
    chunk_id: int
    similarity: float


class ChatResponseModel(BaseModel):
    """Response from chat endpoint."""
    answer: str
    citations: List[CitationResponse]
    confidence: str = Field(..., description="Confidence level: high, medium, or low")
    filters_applied: dict = Field(default_factory=dict)

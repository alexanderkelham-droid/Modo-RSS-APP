"""
Pydantic models for ingestion API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IngestionRunResponse(BaseModel):
    """Response model for ingestion run."""
    
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    stats: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class IngestionRunListResponse(BaseModel):
    """Response model for list of ingestion runs."""
    
    runs: List[IngestionRunResponse]
    total: int


class IngestionStatsSchema(BaseModel):
    """Schema for ingestion statistics."""
    
    new: int = Field(description="Number of new articles")
    updated: int = Field(description="Number of updated articles")
    skipped: int = Field(description="Number of skipped articles")
    failed_sources: List[Dict[str, Any]] = Field(description="List of failed sources")
    total_sources: int = Field(description="Total sources processed")

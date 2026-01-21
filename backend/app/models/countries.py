"""
Pydantic models for country statistics API.
"""

from typing import List
from pydantic import BaseModel


class CountryStats(BaseModel):
    """Country statistics."""
    country_code: str
    country_name: str
    article_count: int


class CountryListResponse(BaseModel):
    """List of countries with article counts."""
    items: List[CountryStats]
    days: int
    total_articles: int

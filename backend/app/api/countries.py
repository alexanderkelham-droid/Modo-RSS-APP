"""
API endpoints for country statistics.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import Article
from app.models.countries import CountryListResponse, CountryStats
from app.services.nlp.country_data import COUNTRY_KEYWORDS

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("", response_model=CountryListResponse)
async def list_countries(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    List countries seen in articles with counts for the last N days.
    
    Returns countries ordered by article count (descending).
    """
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query to get all articles in date range with country codes
    query = select(
        Article.country_codes
    ).where(
        Article.published_at >= cutoff_date,
        Article.country_codes.isnot(None),
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Count articles per country
    country_counts = {}
    total_articles = 0
    
    for row in rows:
        if row.country_codes:
            total_articles += 1
            for country_code in row.country_codes:
                country_counts[country_code] = country_counts.get(country_code, 0) + 1
    
    # Build response items
    items = []
    for country_code, count in country_counts.items():
        # Get country name from COUNTRY_KEYWORDS
        country_name = _get_country_name(country_code)
        
        items.append(CountryStats(
            country_code=country_code,
            country_name=country_name,
            article_count=count,
        ))
    
    # Sort by count (descending)
    items.sort(key=lambda x: x.article_count, reverse=True)
    
    return CountryListResponse(
        items=items,
        days=days,
        total_articles=total_articles,
    )


def _get_country_name(country_code: str) -> str:
    """Get human-readable country name from code."""
    # Map of country codes to names
    country_names = {
        "US": "United States",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
        "ES": "Spain",
        "IT": "Italy",
        "NL": "Netherlands",
        "BE": "Belgium",
        "SE": "Sweden",
        "NO": "Norway",
        "DK": "Denmark",
        "FI": "Finland",
        "PL": "Poland",
        "CN": "China",
        "IN": "India",
        "JP": "Japan",
        "KR": "South Korea",
        "AU": "Australia",
        "NZ": "New Zealand",
        "CA": "Canada",
        "MX": "Mexico",
        "BR": "Brazil",
        "AR": "Argentina",
        "CL": "Chile",
        "ZA": "South Africa",
        "NG": "Nigeria",
        "KE": "Kenya",
        "EG": "Egypt",
        "SA": "Saudi Arabia",
        "AE": "United Arab Emirates",
        "IL": "Israel",
        "TR": "Turkey",
        "RU": "Russia",
        "UA": "Ukraine",
        "GE": "Georgia",
        "KP": "North Korea",
        "VN": "Vietnam",
        "TH": "Thailand",
        "ID": "Indonesia",
        "MY": "Malaysia",
        "SG": "Singapore",
        "PH": "Philippines",
        "PK": "Pakistan",
        "BD": "Bangladesh",
        "LK": "Sri Lanka",
        "NP": "Nepal",
        "MM": "Myanmar",
        "KH": "Cambodia",
        "LA": "Laos",
    }
    
    return country_names.get(country_code, country_code)

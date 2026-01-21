"""
Brief Generation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.ai.brief_generator import BriefGenerator, BriefRequest
from app.services.rag.chat_provider import OpenAIChatProvider
from app.settings import settings

router = APIRouter(prefix="/briefs", tags=["briefs"])


class GenerateBriefRequest(BaseModel):
    """Request model for brief generation."""
    country_code: Optional[str] = Field(None, description="Country code (e.g., 'US', 'UK')")
    topic: Optional[str] = Field(None, description="Topic filter (e.g., 'renewable_energy')")
    days: int = Field(7, description="Number of days to look back", ge=1, le=365)
    max_articles: int = Field(15, description="Maximum articles to include", ge=1, le=50)


class GenerateBriefResponse(BaseModel):
    """Response model for brief generation."""
    brief: str
    article_count: int
    country_code: Optional[str]
    topic: Optional[str]
    date_range: dict


def get_brief_generator() -> BriefGenerator:
    """Dependency to get brief generator."""
    chat_provider = OpenAIChatProvider(
        api_key=settings.OPENAI_API_KEY,
    )
    return BriefGenerator(chat_provider=chat_provider)


@router.post("/generate", response_model=GenerateBriefResponse)
async def generate_brief(
    request: GenerateBriefRequest,
    db: AsyncSession = Depends(get_db),
    generator: BriefGenerator = Depends(get_brief_generator),
):
    """
    Generate an AI brief from recent articles.
    
    The system will:
    1. Fetch articles matching the filters (country, topic, date range)
    2. Summarize and analyze the articles using AI
    3. Generate a structured brief with key developments and insights
    4. Return the brief with metadata
    
    Example usage:
    - Country brief: `{"country_code": "US", "days": 7}`
    - Topic brief: `{"topic": "renewable_energy", "days": 14}`
    - Combined: `{"country_code": "UK", "topic": "solar", "days": 30}`
    """
    try:
        # Create brief request
        brief_request = BriefRequest(
            country_code=request.country_code,
            topic=request.topic,
            days=request.days,
            max_articles=request.max_articles,
        )
        
        # Generate brief
        response = await generator.generate_brief(
            db=db,
            request=brief_request,
        )
        
        return GenerateBriefResponse(
            brief=response.brief,
            article_count=response.article_count,
            country_code=response.country_code,
            topic=response.topic,
            date_range=response.date_range,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_brief(
    country_code: str,
    db: AsyncSession = Depends(get_db),
    generator: BriefGenerator = Depends(get_brief_generator),
):
    """
    Get or generate the latest brief for a country.
    
    Returns cached brief if generated within last 24 hours, otherwise generates new one.
    """
    try:
        # For now, just generate a new brief each time
        # TODO: Add caching/storage in database
        brief_request = BriefRequest(
            country_code=country_code,
            days=7,
            max_articles=15,
        )
        
        response = await generator.generate_brief(db=db, request=brief_request)
        
        return {
            "content": response.brief,
            "generated_at": response.date_range["end"],
            "article_count": response.article_count,
            "country_code": country_code,
        }
    except Exception as e:
        # Return empty if generation fails
        return {
            "content": None,
            "generated_at": None,
            "article_count": 0,
            "country_code": country_code,
        }

"""
API endpoints for ingestion management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db import get_db
from app.services.ingest import IngestionService
from app.models.ingestion import IngestionRunResponse, IngestionRunListResponse

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/run", response_model=IngestionRunResponse)
async def trigger_ingestion(db: AsyncSession = Depends(get_db)):
    """
    Trigger a manual ingestion run for all enabled sources.
    
    Returns statistics about the ingestion run.
    """
    service = IngestionService(db)
    try:
        run = await service.run_ingestion()
        
        # Auto-generate AI briefs for major countries after ingestion
        from app.services.ai.brief_generator import BriefGenerator, BriefRequest
        from app.services.rag.chat_provider import OpenAIChatProvider
        from app.settings import settings
        from datetime import datetime, timedelta
        
        try:
            chat_provider = OpenAIChatProvider(api_key=settings.OPENAI_API_KEY)
            generator = BriefGenerator(chat_provider=chat_provider)
            major_countries = ['US', 'GB', 'DE', 'CN', 'IN', 'AU']
            
            for country_code in major_countries:
                try:
                    brief_request = BriefRequest(
                        country_code=country_code,
                        days=7,
                        max_articles=15
                    )
                    await generator.generate_brief(db=db, request=brief_request)
                except Exception as e:
                    # Log but don't fail the whole ingestion
                    print(f"Failed to generate brief for {country_code}: {str(e)}")
        except Exception as e:
            # If OpenAI setup fails, just skip brief generation
            print(f"Brief generation skipped: {str(e)}")
        
        return IngestionRunResponse(
            id=run.id,
            started_at=run.started_at,
            finished_at=run.finished_at,
            status=run.status,
            stats=run.stats,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/runs", response_model=IngestionRunListResponse)
async def list_ingestion_runs(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    List recent ingestion runs with their statistics.
    """
    from sqlalchemy import select, desc
    from app.db.models import IngestionRun
    
    result = await db.execute(
        select(IngestionRun)
        .order_by(desc(IngestionRun.started_at))
        .limit(limit)
        .offset(offset)
    )
    runs = result.scalars().all()
    
    return IngestionRunListResponse(
        runs=[
            IngestionRunResponse(
                id=run.id,
                started_at=run.started_at,
                finished_at=run.finished_at,
                status=run.status,
                stats=run.stats,
            )
            for run in runs
        ],
        total=len(runs),
    )


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
async def get_ingestion_run(run_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific ingestion run.
    """
    from sqlalchemy import select
    from app.db.models import IngestionRun
    
    result = await db.execute(
        select(IngestionRun).where(IngestionRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    
    return IngestionRunResponse(
        id=run.id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        stats=run.stats,
    )

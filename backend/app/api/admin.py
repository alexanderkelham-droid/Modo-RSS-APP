"""
API endpoint to process existing articles (chunk and embed).
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict

from app.db.session import get_db
from app.db.models import Article, ArticleChunk
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from app.settings import settings

router = APIRouter(prefix="/admin", tags=["admin"])


async def process_articles_background(db: AsyncSession):
    """Background task to process articles."""
    chunking_service = ChunkingService()
    embedding_provider = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
    
    # Get articles without chunks
    subquery = select(ArticleChunk.article_id).distinct().subquery()
    query = select(Article).where(~Article.id.in_(select(subquery)))
    result = await db.execute(query)
    articles = result.scalars().all()
    
    total_chunks = 0
    
    for article in articles:
        if article.content_text:
            chunks = chunking_service.chunk_text(
                text=article.content_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            
            for chunk_num, chunk_text in enumerate(chunks):
                embedding = await embedding_provider.generate_embedding(chunk_text)
                
                chunk = ArticleChunk(
                    article_id=article.id,
                    chunk_number=chunk_num,
                    content=chunk_text,
                    embedding=embedding,
                )
                db.add(chunk)
                total_chunks += 1
            
            await db.commit()


@router.post("/process-articles")
async def trigger_article_processing(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Trigger processing of existing articles (chunking and embedding).
    
    This will run in the background and process all articles that don't have chunks yet.
    """
    # Count articles without chunks
    subquery = select(ArticleChunk.article_id).distinct().subquery()
    query = select(Article).where(~Article.id.in_(select(subquery)))
    result = await db.execute(query)
    articles = result.scalars().all()
    
    count = len(articles)
    
    if count == 0:
        return {
            "status": "success",
            "message": "All articles already processed",
            "articles_to_process": 0
        }
    
    return {
        "status": "info",
        "message": f"Found {count} articles to process. Use a worker process or script to process them.",
        "articles_to_process": count,
        "note": "Background processing not implemented - run scripts/process_articles.py instead"
    }

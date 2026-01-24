"""
API endpoint to process existing articles (chunk and embed).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict
import asyncio

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Article, ArticleChunk
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from app.settings import settings

router = APIRouter(prefix="/admin", tags=["admin"])


async def process_articles_task():
    """Process articles in a separate task."""
    async with AsyncSessionLocal() as db:
        chunking_service = ChunkingService(
            min_chunk_size=800,
            max_chunk_size=1200,
            overlap=100,
        )
        embedding_provider = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
        
        # Get articles without chunks - load all data eagerly
        subquery = select(ArticleChunk.article_id).distinct().subquery()
        query = select(Article.id, Article.content_text).where(
            ~Article.id.in_(select(subquery)),
            Article.content_text.isnot(None)
        )
        result = await db.execute(query)
        articles_data = result.all()
        
        total_chunks = 0
        processed = 0
        
        for article_id, content_text in articles_data:
            try:
                # Chunk text
                text_chunks = chunking_service.chunk_text(text=content_text)
                
                # Create chunks with embeddings
                for chunk_obj in text_chunks:
                    embedding = await embedding_provider.generate_embedding(chunk_obj.text)
                    
                    chunk = ArticleChunk(
                        article_id=article_id,
                        chunk_number=chunk_obj.chunk_index,
                        content=chunk_obj.text,
                        embedding=embedding,
                    )
                    db.add(chunk)
                    total_chunks += 1
                
                await db.commit()
                processed += 1
                
                # Log progress every 10 articles
                if processed % 10 == 0:
                    print(f"Processed {processed}/{len(articles_data)} articles, {total_chunks} chunks")
                
            except Exception as e:
                await db.rollback()
                print(f"Error processing article: {str(e)}")
                continue
        
        print(f"✅ Processing complete: {processed} articles, {total_chunks} total chunks")


@router.get("/process-articles")
async def trigger_article_processing(
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Trigger processing of existing articles (chunking and embedding).
    
    This will process all articles that don't have chunks yet.
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
    
    # Start processing in background
    asyncio.create_task(process_articles_task())
    
    return {
        "status": "processing",
        "message": f"Started processing {count} articles. This will take a few minutes.",
        "articles_to_process": count,
        "note": "Processing in background. Check logs for progress."
    }

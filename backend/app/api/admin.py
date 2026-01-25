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
from app.ingest.pipeline import run_full_ingestion_pipeline

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
                
                # Get all chunk texts
                chunk_texts = [chunk_obj.text for chunk_obj in text_chunks]
                
                # Generate embeddings in batch
                embeddings = await embedding_provider.embed(chunk_texts)
                
                # Create chunks with embeddings
                for chunk_obj, embedding in zip(text_chunks, embeddings):
                    chunk = ArticleChunk(
                        article_id=article_id,
                        chunk_index=chunk_obj.chunk_index,
                        text=chunk_obj.text,
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


@router.post("/run-pipeline")
async def trigger_pipeline() -> Dict:
    """
    Trigger the full ingestion pipeline.
    
    This will:
    - Fetch articles from all enabled sources (RSS and web scrapers)
    - Extract content from article URLs
    - Tag articles with countries and topics
    - Create chunks
    - Generate embeddings
    
    The pipeline runs in the background and may take several minutes.
    Check the server logs for progress.
    """
    # Start pipeline in background
    asyncio.create_task(run_full_ingestion_pipeline())
    
    return {
        "status": "started",
        "message": "Ingestion pipeline started in background",
        "note": "This may take 5-15 minutes. Check server logs for progress."
    }

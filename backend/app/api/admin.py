"""
API endpoint to process existing articles (chunk and embed).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict
import asyncio

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Article, ArticleChunk, Source
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


@router.get("/run-pipeline")
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


@router.get("/check-neso")
async def check_neso_articles(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Check NESO articles in the database.
    
    Returns count and sample of NESO articles.
    """
    # Find NESO source
    result = await db.execute(select(Source).where(Source.name == "NESO"))
    neso_source = result.scalar_one_or_none()
    
    if not neso_source:
        return {
            "error": "NESO source not found",
            "hint": "Run the pipeline first to add NESO source"
        }
    
    # Count articles
    result = await db.execute(
        select(func.count(Article.id)).where(Article.source_id == neso_source.id)
    )
    article_count = result.scalar()
    
    # Count chunks
    result = await db.execute(
        select(func.count(ArticleChunk.id))
        .join(Article)
        .where(Article.source_id == neso_source.id)
    )
    chunk_count = result.scalar()
    
    # Get sample articles
    result = await db.execute(
        select(Article)
        .where(Article.source_id == neso_source.id)
        .limit(5)
    )
    sample_articles = result.scalars().all()
    
    return {
        "neso_source_id": neso_source.id,
        "total_articles": article_count,
        "total_chunks": chunk_count,
        "sample_articles": [
            {
                "title": article.title,
                "url": article.url,
                "country_codes": article.country_codes,
                "topic_tags": article.topic_tags,
                "has_content": article.content_text is not None,
                "has_embedding": article.embedding is not None,
            }
            for article in sample_articles
        ]
    }


@router.get("/embed-chunks")
async def embed_existing_chunks(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Generate embeddings for chunks that don't have them yet.
    
    This is useful when chunks were created but embedding failed.
    """
    # Count chunks without embeddings
    result = await db.execute(
        select(func.count(ArticleChunk.id))
        .where(ArticleChunk.embedding.is_(None))
    )
    chunks_without_embeddings = result.scalar()
    
    if chunks_without_embeddings == 0:
        return {
            "status": "success",
            "message": "All chunks already have embeddings",
            "chunks_processed": 0
        }
    
    # Start embedding task
    async def embed_task():
        async with AsyncSessionLocal() as task_db:
            from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
            from app.settings import settings
            
            provider = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
            
            # Get chunks without embeddings
            result = await task_db.execute(
                select(ArticleChunk)
                .where(ArticleChunk.embedding.is_(None))
            )
            chunks = result.scalars().all()
            
            print(f"🔄 Starting embedding generation for {len(chunks)} chunks...")
            
            # Process in batches of 100
            batch_size = 100
            total_embedded = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                chunk_texts = [chunk.text for chunk in batch]
                
                try:
                    print(f"  Generating embeddings for batch {i//batch_size + 1} ({len(batch)} chunks)...")
                    embeddings = await provider.embed(chunk_texts)
                    
                    for chunk, embedding in zip(batch, embeddings):
                        chunk.embedding = embedding
                    
                    await task_db.commit()
                    total_embedded += len(embeddings)
                    print(f"  ✅ Batch {i//batch_size + 1} complete ({total_embedded}/{len(chunks)} total)")
                    
                except Exception as e:
                    print(f"  ❌ Batch {i//batch_size + 1} failed: {e}")
                    await task_db.rollback()
                    import traceback
                    print(traceback.format_exc())
            
            print(f"✅ Embedding generation complete: {total_embedded}/{len(chunks)} chunks embedded")
    
    asyncio.create_task(embed_task())
    
    return {
        "status": "started",
        "message": f"Started embedding generation for {chunks_without_embeddings} chunks",
        "chunks_to_process": chunks_without_embeddings,
        "note": "Processing in background. Check server logs for progress."
    }

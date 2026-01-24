"""
Process existing articles: chunk and generate embeddings.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Article, ArticleChunk
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from app.settings import settings


async def process_existing_articles():
    """Process existing articles: chunk and generate embeddings."""
    
    print("\n🚀 Processing existing articles...")
    print("=" * 80)
    
    # Initialize services
    chunking_service = ChunkingService()
    embedding_provider = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
    
    async with AsyncSessionLocal() as db:
        # Get all articles without chunks
        query = select(Article).where(
            ~Article.id.in_(
                select(ArticleChunk.article_id).distinct()
            )
        )
        result = await db.execute(query)
        articles = result.scalars().all()
        
        print(f"📄 Found {len(articles)} articles without chunks\n")
        
        if not articles:
            print("✅ All articles already processed!")
            return
        
        total_chunks = 0
        total_embeddings = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\r[{i}/{len(articles)}] Processing: {article.title[:60]}...", end="", flush=True)
            
            try:
                # Chunk article
                if article.content_text:
                    chunks = chunking_service.chunk_text(
                        text=article.content_text,
                        chunk_size=settings.CHUNK_SIZE,
                        chunk_overlap=settings.CHUNK_OVERLAP,
                    )
                    
                    # Create and embed chunks
                    for chunk_num, chunk_text in enumerate(chunks):
                        # Generate embedding
                        embedding = await embedding_provider.generate_embedding(chunk_text)
                        
                        # Create chunk
                        chunk = ArticleChunk(
                            article_id=article.id,
                            chunk_number=chunk_num,
                            content=chunk_text,
                            embedding=embedding,
                        )
                        db.add(chunk)
                        total_chunks += 1
                        total_embeddings += 1
                    
                    await db.commit()
            
            except Exception as e:
                print(f"\n❌ Error processing article {article.id}: {e}")
                await db.rollback()
                continue
        
        print(f"\n\n✅ Processing complete!")
        print(f"📊 Created {total_chunks} chunks with {total_embeddings} embeddings")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(process_existing_articles())

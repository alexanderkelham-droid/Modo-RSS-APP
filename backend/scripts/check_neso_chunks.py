"""Check NESO article chunks in database."""
import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.models import Source, Article, ArticleChunk


async def main():
    async with AsyncSessionLocal() as db:
        # Get NESO source
        result = await db.execute(select(Source).where(Source.name == "NESO"))
        neso_source = result.scalar_one_or_none()
        
        if not neso_source:
            print("❌ NESO source not found")
            return
        
        print(f"✅ NESO source found (ID: {neso_source.id})")
        
        # Count chunks for NESO articles
        chunk_count_query = (
            select(func.count(ArticleChunk.id))
            .join(Article)
            .where(Article.source_id == neso_source.id)
        )
        chunk_result = await db.execute(chunk_count_query)
        chunk_count = chunk_result.scalar()
        
        print(f"\n📊 NESO article chunks in database: {chunk_count}")
        
        if chunk_count == 0:
            print("\n⚠️  No chunks found for NESO articles!")
            print("The pipeline created articles but failed during chunking phase.")
        else:
            # Show sample chunks
            sample_chunks_query = (
                select(ArticleChunk, Article.title)
                .join(Article)
                .where(Article.source_id == neso_source.id)
                .limit(3)
            )
            sample_result = await db.execute(sample_chunks_query)
            sample_chunks = sample_result.all()
            
            print("\n📦 Sample chunks:")
            for chunk, article_title in sample_chunks:
                print(f"\n  - Article: {article_title}")
                print(f"    Chunk index: {chunk.chunk_index}")
                print(f"    Text preview: {chunk.text[:100]}...")
                print(f"    Has embedding: {'Yes' if chunk.embedding else 'No'}")


if __name__ == "__main__":
    asyncio.run(main())

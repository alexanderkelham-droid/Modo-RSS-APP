"""Test generating embeddings for ingested articles."""

import asyncio
from app.db.session import get_db
from app.db.models import Article, Source
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from sqlalchemy import select


async def main():
    """Test embedding generation for Energy Storage News articles."""
    async for db in get_db():
        # Get articles without embeddings from Energy Storage News
        result = await db.execute(
            select(Source).where(Source.name == "Energy Storage News")
        )
        source = result.scalar_one_or_none()
        
        if not source:
            print("❌ Energy Storage News source not found")
            return
        
        # Get articles with content but no embeddings
        result = await db.execute(
            select(Article)
            .where(Article.source_id == source.id)
            .where(Article.content_text.isnot(None))
            .where(Article.embedding.is_(None))
            .limit(3)
        )
        articles = result.scalars().all()
        
        if not articles:
            print("ℹ️  No articles need embeddings (either no content or already have embeddings)")
            # Check total articles
            result = await db.execute(
                select(Article).where(Article.source_id == source.id)
            )
            total = len(result.scalars().all())
            print(f"   Total articles from Energy Storage News: {total}")
            return
        
        print(f"🔄 Generating embeddings for {len(articles)} articles from Energy Storage News\n")
        
        # Initialize embedding provider
        embedding_provider = OpenAIEmbeddingProvider()
        
        success_count = 0
        failed_count = 0
        
        for i, article in enumerate(articles, 1):
            print(f"[{i}/{len(articles)}] Processing: {article.title[:60]}...")
            
            try:
                # Generate embedding for article title + content
                text = f"{article.title}\n\n{article.content_text[:2000]}"  # Limit to 2000 chars for testing
                
                # OpenAIEmbeddingProvider.embed() expects a list of texts
                embeddings = await embedding_provider.embed([text])
                
                if embeddings and len(embeddings) > 0:
                    article.embedding = embeddings[0]  # Get first (and only) embedding
                    success_count += 1
                    print(f"   ✅ Generated embedding (dimension: {len(embeddings[0])})")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to generate embedding")
                    
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error: {e}")
        
        # Commit changes
        await db.commit()
        
        print(f"\n📊 Embedding generation completed!")
        print(f"   Success: {success_count}")
        print(f"   Failed: {failed_count}")
        
        # Verify embeddings were saved
        result = await db.execute(
            select(Article)
            .where(Article.source_id == source.id)
            .where(Article.embedding.isnot(None))
        )
        with_embeddings = len(result.scalars().all())
        
        print(f"\n✅ Total articles with embeddings: {with_embeddings}")
        
        break


if __name__ == "__main__":
    asyncio.run(main())

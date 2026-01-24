"""
Full ingestion pipeline: RSS fetch -> extraction -> tagging -> chunking -> embeddings.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models import Source, Article, ArticleChunk
from app.services.ingest.ingestion_service import IngestionService
from app.services.ingest.fetcher import RSSFetcher
from app.services.ingest.rss_parser import RSSParser
from app.services.ingest.content_extractor import ContentExtractor
from app.services.nlp.country_tagger import CountryTagger
from app.services.nlp.topic_tagger import TopicTagger
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from app.settings import Settings

logger = logging.getLogger(__name__)


class IngestionMetrics:
    """Structured metrics for ingestion run."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.sources_processed = 0
        self.articles_fetched = 0
        self.articles_new = 0
        self.articles_updated = 0
        self.articles_extracted = 0
        self.articles_tagged = 0
        self.chunks_created = 0
        self.chunks_embedded = 0
        self.errors = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "start_time": self.start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "sources_processed": self.sources_processed,
            "articles_fetched": self.articles_fetched,
            "articles_new": self.articles_new,
            "articles_updated": self.articles_updated,
            "articles_extracted": self.articles_extracted,
            "articles_tagged": self.articles_tagged,
            "chunks_created": self.chunks_created,
            "chunks_embedded": self.chunks_embedded,
            "errors": len(self.errors),
            "error_details": self.errors[:10],  # First 10 errors
        }
    
    def log_summary(self):
        """Log metrics summary."""
        metrics = self.to_dict()
        logger.info(
            f"Ingestion completed in {metrics['duration_seconds']}s: "
            f"{metrics['sources_processed']} sources, "
            f"{metrics['articles_new']} new articles, "
            f"{metrics['chunks_created']} chunks, "
            f"{metrics['chunks_embedded']} embeddings, "
            f"{metrics['errors']} errors"
        )
        if self.errors:
            logger.warning(f"Errors encountered: {self.errors[:5]}")


async def run_full_ingestion_pipeline() -> Dict[str, Any]:
    """
    Run complete ingestion pipeline for all enabled sources.
    
    Steps:
    1. Fetch RSS feeds
    2. Parse articles
    3. Extract content (readability)
    4. Tag countries and topics
    5. Chunk articles
    6. Generate embeddings
    
    Returns:
        Dictionary with ingestion metrics
    """
    metrics = IngestionMetrics()
    logger.info("=" * 80)
    logger.info("Starting full ingestion pipeline")
    logger.info("=" * 80)
    
    # Initialize services
    settings = Settings()
    fetcher = RSSFetcher()
    parser = RSSParser()
    extractor = ContentExtractor()
    country_tagger = CountryTagger()
    topic_tagger = TopicTagger()
    chunking_service = ChunkingService()
    embedding_provider = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
    
    async with AsyncSessionLocal() as db:
        # Get enabled sources
        query = select(Source).where(Source.enabled == True)
        result = await db.execute(query)
        sources = result.scalars().all()
        
        if not sources:
            logger.warning("No enabled sources found")
            return metrics.to_dict()
        
        logger.info(f"Found {len(sources)} enabled sources")
        
        # Process each source
        for source in sources:
            try:
                logger.info(f"Processing source: {source.name}")
                metrics.sources_processed += 1
                
                # Step 1: Fetch RSS feed
                try:
                    xml_content = await fetcher.fetch(source.rss_url)
                except Exception as e:
                    error_msg = f"Failed to fetch {source.name}: {str(e)}"
                    logger.error(error_msg)
                    metrics.errors.append(error_msg)
                    continue
                
                # Step 2: Parse articles
                try:
                    parsed_articles = parser.parse(xml_content, source.rss_url)
                    metrics.articles_fetched += len(parsed_articles)
                    logger.info(f"  Fetched {len(parsed_articles)} articles")
                except Exception as e:
                    error_msg = f"Failed to parse {source.name}: {str(e)}"
                    logger.error(error_msg)
                    metrics.errors.append(error_msg)
                    continue
                
                # Step 3-6: Process each article
                for parsed_article in parsed_articles:
                    try:
                        # Upsert article
                        existing_query = select(Article).where(
                            Article.url == parsed_article["url"]
                        )
                        existing_result = await db.execute(existing_query)
                        existing_article = existing_result.scalar_one_or_none()
                        
                        if existing_article:
                            # Skip if already has content
                            if existing_article.content_text:
                                continue
                            article = existing_article
                            metrics.articles_updated += 1
                        else:
                            # Create new article
                            article = Article(
                                source_id=source.id,
                                title=parsed_article["title"],
                                url=parsed_article["url"],
                                content_hash=parsed_article["content_hash"],
                                published_at=parsed_article.get("published_at"),
                                raw_summary=parsed_article.get("summary"),
                            )
                            db.add(article)
                            metrics.articles_new += 1
                        
                        await db.flush()
                        
                        # Step 3: Extract content
                        try:
                            extracted = await extractor.extract(article.url)
                            article.content_text = extracted["content"]
                            article.language = extracted["language"]
                            metrics.articles_extracted += 1
                        except Exception as e:
                            logger.warning(f"  Extraction failed for {article.url}: {e}")
                            continue
                        
                        # Step 4: Tag countries and topics
                        try:
                            text_to_tag = f"{article.title}\n\n{article.content_text or ''}"
                            
                            # Country tagging
                            country_results = country_tagger.tag(text_to_tag, article.title)
                            article.country_codes = [c["code"] for c in country_results]
                            
                            # Topic tagging
                            topic_results = topic_tagger.tag(text_to_tag)
                            article.topic_tags = [t["topic_id"] for t in topic_results]
                            
                            metrics.articles_tagged += 1
                        except Exception as e:
                            logger.warning(f"  Tagging failed for {article.url}: {e}")
                        
                        await db.flush()
                        
                        # Step 5: Chunk article
                        if article.content_text:
                            try:
                                # Delete existing chunks
                                existing_chunks_query = select(ArticleChunk).where(
                                    ArticleChunk.article_id == article.id
                                )
                                existing_chunks_result = await db.execute(existing_chunks_query)
                                existing_chunks = existing_chunks_result.scalars().all()
                                for chunk in existing_chunks:
                                    await db.delete(chunk)
                                
                                # Create new chunks
                                chunks = chunking_service.chunk_article(
                                    article_id=article.id,
                                    title=article.title,
                                    content=article.content_text,
                                )
                                
                                chunk_texts = []
                                chunk_objects = []
                                
                                for chunk_data in chunks:
                                    chunk = ArticleChunk(
                                        article_id=article.id,
                                        chunk_index=chunk_data["chunk_index"],
                                        text=chunk_data["text"],
                                        char_count=chunk_data["char_count"],
                                        # Denormalize for faster filtering
                                        country_codes=article.country_codes,
                                        topic_tags=article.topic_tags,
                                        published_at=article.published_at,
                                    )
                                    chunk_objects.append(chunk)
                                    chunk_texts.append(chunk_data["text"])
                                
                                metrics.chunks_created += len(chunk_objects)
                                
                                # Step 6: Generate embeddings in batch
                                if chunk_texts:
                                    try:
                                        embeddings = await embedding_provider.embed_batch(chunk_texts)
                                        
                                        for chunk_obj, embedding in zip(chunk_objects, embeddings):
                                            chunk_obj.embedding = embedding
                                        
                                        metrics.chunks_embedded += len(embeddings)
                                    except Exception as e:
                                        logger.warning(f"  Embedding failed for {article.url}: {e}")
                                        # Still save chunks without embeddings
                                
                                # Save chunks
                                for chunk_obj in chunk_objects:
                                    db.add(chunk_obj)
                                
                            except Exception as e:
                                logger.warning(f"  Chunking failed for {article.url}: {e}")
                        
                        await db.commit()
                        
                    except Exception as e:
                        error_msg = f"Failed to process article {parsed_article.get('url')}: {str(e)}"
                        logger.error(error_msg)
                        metrics.errors.append(error_msg)
                        await db.rollback()
                        continue
                
            except Exception as e:
                error_msg = f"Failed to process source {source.name}: {str(e)}"
                logger.error(error_msg)
                metrics.errors.append(error_msg)
                continue
    
    # Log summary
    logger.info("=" * 80)
    metrics.log_summary()
    logger.info("=" * 80)
    
    return metrics.to_dict()


if __name__ == "__main__":
    # Allow running as script for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(run_full_ingestion_pipeline())

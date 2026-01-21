"""
Main RSS ingestion service orchestrating feed fetching, parsing, and storage.
"""

from datetime import datetime
from typing import List, Dict, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Source, Article, IngestionRun
from app.services.ingest.fetcher import RSSFetcher, FeedFetchError
from app.services.ingest.rss_parser import RSSParser, RSSEntry
from app.services.ingest.content_extractor import ContentExtractor, ContentExtractionError
from app.services.nlp.country_tagger import CountryTagger
from app.services.nlp.topic_tagger import TopicTagger
from app.settings import settings


class IngestionStats:
    """Statistics for an ingestion run."""
    
    def __init__(self):
        self.new_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.failed_sources: List[Dict] = []
        self.extraction_failed_count = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "new": self.new_count,
            "updated": self.updated_count,
            "skipped": self.skipped_count,
            "failed_sources": self.failed_sources,
            "extraction_failed": self.extraction_failed_count,
            "total_sources": self.new_count + self.updated_count + self.skipped_count + len(self.failed_sources),
        }


class IngestionService:
    """Service for ingesting RSS feeds into the database."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize ingestion service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.fetcher = RSSFetcher(
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            user_agent=settings.USER_AGENT,
        )
        self.extractor = ContentExtractor(
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            user_agent=settings.USER_AGENT,
        )
        self.topic_tagger = TopicTagger(max_topics=3)
        self.country_tagger = CountryTagger(max_countries=3)
        self.parser = RSSParser()
    
    async def get_enabled_sources(self) -> List[Source]:
        """
        Fetch all enabled RSS sources from database.
        
        Returns:
            List of enabled Source objects
        """
        result = await self.db.execute(
            select(Source).where(Source.enabled == True)
        )
        return list(result.scalars().all())
    
    async def upsert_article(
        self,
        source_id: int,
        entry: RSSEntry,
    ) -> Tuple[bool, bool]:
        """
        Insert or update article in database.
        
        Args:
            source_id: ID of the source
            entry: Parsed RSS entry
            
        Returns:
            Tuple of (was_inserted, was_updated)
        """
        # Compute content hash
        content_hash = self.parser.compute_content_hash(
            entry.title,
            entry.url,
            entry.summary
        )
        
        # Check if article exists
        result = await self.db.execute(
            select(Article).where(Article.url == entry.url)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Check if content changed
            if existing.hash == content_hash:
                return (False, False)  # No changes, skip
            
            # Update existing article
            existing.title = entry.title
            existing.raw_summary = entry.summary
            existing.published_at = entry.published_at
            existing.hash = content_hash
            existing.fetched_at = datetime.utcnow()
            
            return (False, True)  # Updated
        else:
            # Insert new article
            article = Article(
                source_id=source_id,
                title=entry.title,
                url=entry.url,
                published_at=entry.published_at,
                fetched_at=datetime.utcnow(),
                raw_summary=entry.summary,
                hash=content_hash,
            )
            self.db.add(article)
            
            return (True, False)  # Inserted
    
    async def ingest_source(
        self,
        source: Source,
        stats: IngestionStats,
    ) -> None:
        """
        Ingest articles from a single RSS source.
        
        Args:
            source: Source object to ingest
            stats: Statistics object to update
        """
        try:
            # Fetch feed content
            feed_content = await self.fetcher.fetch_feed(source.rss_url)
            
            # Parse entries
            entries = self.parser.parse_feed(feed_content)
            
            # Limit to 10 articles per source
            entries = entries[:10]
            
            # Process each entry
            for entry in entries:
                try:
                    # Check if article already exists
                    result = await self.db.execute(
                        select(Article).where(Article.url == entry.url)
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing article
                        existing.title = entry.title
                        existing.published_at = entry.published_at
                        stats.updated_count += 1
                    else:
                        # Create new article
                        article = Article(
                            source_id=source.id,
                            title=entry.title,
                            url=entry.url,
                            published_at=entry.published_at,
                            raw_summary=entry.summary,
                        )
                        self.db.add(article)
                        await self.db.flush()  # Get the article ID
                        stats.new_count += 1
                        
                        # Extract content for new articles (skip paywalled sources and Google News)
                        is_google_news = 'news.google.com' in entry.url
                        
                        if source.type != 'paywalled' and not is_google_news:
                            try:
                                # Extract content
                                content, language = await self.extractor.extract_article(entry.url)
                                
                                if content:
                                    article.content_text = content
                                    article.language = language
                                    
                                    # Tag countries
                                    country_codes, country_metadata = self.country_tagger.tag_article(
                                        article.title,
                                        content
                                    )
                                    article.country_codes = country_codes if country_codes else None
                                    
                                    # Tag topics
                                    topic_tags = self.topic_tagger.tag_article(
                                        article.title,
                                        content
                                    )
                                    article.topic_tags = topic_tags if topic_tags else None
                                    
                                    # Store region metadata if present
                                    if country_metadata:
                                        if article.article_metadata is None:
                                            article.article_metadata = {}
                                        article.article_metadata.update(country_metadata)
                                else:
                                    stats.extraction_failed_count += 1
                                    print(f"Content extraction returned empty for {entry.url}")
                                
                            except ContentExtractionError as e:
                                stats.extraction_failed_count += 1
                                print(f"Content extraction failed for {entry.url}: {e}")
                            except Exception as e:
                                stats.extraction_failed_count += 1
                                print(f"Unexpected error extracting content for {entry.url}: {e}")
                        
                        elif is_google_news:
                            # For Google News URLs, use summary as content and tag from title/summary
                            if article.raw_summary:
                                # Tag countries from title and summary
                                country_codes, country_metadata = self.country_tagger.tag_article(
                                    article.title,
                                    article.raw_summary
                                )
                                article.country_codes = country_codes if country_codes else None
                                
                                # Tag topics from title and summary
                                topic_tags = self.topic_tagger.tag_article(
                                    article.title,
                                    article.raw_summary
                                )
                                article.topic_tags = topic_tags if topic_tags else None
                                
                                # Store region metadata if present
                                if country_metadata:
                                    if article.article_metadata is None:
                                        article.article_metadata = {}
                                    article.article_metadata.update(country_metadata)
                
                except Exception as e:
                    print(f"Error processing entry {entry.url}: {e}")
                    stats.extraction_failed_count += 1
                try:
                    inserted, updated = await self.upsert_article(source.id, entry)
                    
                    if inserted:
                        stats.new_count += 1
                    elif updated:
                        stats.updated_count += 1
                    else:
                        stats.skipped_count += 1
                
                except Exception as e:
                    print(f"Error processing entry {entry.url}: {e}")
                    continue
            
            # Commit after each source
            await self.db.commit()
            
        except FeedFetchError as e:
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": str(e),
            })
            print(f"Failed to fetch source {source.name}: {e}")
        
        except ValueError as e:
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": f"Parse error: {e}",
            })
            print(f"Failed to parse source {source.name}: {e}")
        
        except Exception as e:
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": f"Unexpected error: {e}",
            })
            print(f"Unexpected error with source {source.name}: {e}")
    
    async def run_ingestion(self) -> IngestionRun:
        """
        Run full ingestion cycle for all enabled sources.
        
        Returns:
            IngestionRun object with statistics
        """
        # Create ingestion run record
        run = IngestionRun(
            started_at=datetime.utcnow(),
            status="running",
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        stats = IngestionStats()
        
        try:
            # Get enabled sources
            sources = await self.get_enabled_sources()
            
            if not sources:
                print("No enabled sources found")
                run.status = "completed"
                run.finished_at = datetime.utcnow()
                run.stats = stats.to_dict()
                await self.db.commit()
                return run
            
            # Ingest each source
            for source in sources:
                print(f"Ingesting source: {source.name}")
                await self.ingest_source(source, stats)
            
            # Update run record
            run.status = "completed"
            run.finished_at = datetime.utcnow()
            run.stats = stats.to_dict()
            await self.db.commit()
            
            print(f"Ingestion completed: {stats.new_count} new, {stats.updated_count} updated, "
                  f"{stats.skipped_count} skipped, {len(stats.failed_sources)} failed sources")
            
        except Exception as e:
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.stats = stats.to_dict()
            run.stats["error"] = str(e)
            await self.db.commit()
            print(f"Ingestion failed: {e}")
            raise
        
        return run

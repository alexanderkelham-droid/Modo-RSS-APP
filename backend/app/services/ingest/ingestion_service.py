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
        print(f"\n{'='*60}")
        print(f"Starting ingestion for: {source.name}")
        print(f"URL: {source.rss_url}")
        print(f"Type: {source.type}")
        print(f"{'='*60}\n")
        
        try:
            # Skip Google News sources for now
            if 'news.google.com' in source.rss_url:
                print(f"⏭️  Skipping Google News source: {source.name}")
                return
            
            # Fetch feed content
            print(f"📥 Fetching feed from {source.rss_url[:80]}...")
            feed_content = await self.fetcher.fetch_feed(source.rss_url)
            print(f"✅ Feed fetched successfully ({len(feed_content)} bytes)")
            
            # Parse entries
            print(f"📄 Parsing RSS feed...")
            entries = self.parser.parse_feed(feed_content)
            print(f"✅ Found {len(entries)} entries in feed")
            
            # Limit to 10 articles per source
            entries = entries[:10]
            print(f"📊 Processing {len(entries)} entries (limited to 10)")
            
            # Process each entry
            for idx, entry in enumerate(entries, 1):
                print(f"\n  [{idx}/{len(entries)}] Processing: {entry.title[:60]}...")
                print(f"          URL: {entry.url[:80]}...")
                
                try:
                    # Check if article already exists
                    result = await self.db.execute(
                        select(Article).where(Article.url == entry.url)
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing article
                        print(f"          ♻️  Updating existing article (ID: {existing.id})")
                        existing.title = entry.title
                        existing.published_at = entry.published_at
                        stats.updated_count += 1
                    else:
                        # Create new article
                        print(f"          ✨ Creating new article")
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
                        print(f"          ✅ Article created (ID: {article.id})")
                        
                        # Extract content for new articles (skip paywalled sources)
                        if source.type != 'paywalled':
                            content = None
                            language = None
                            image_url = None
                            
                            try:
                                print(f"          🔍 Extracting content from article...")
                                # Try extracting content from URL
                                content, language, image_url = await self.extractor.extract_article(entry.url)
                                
                                if content:
                                    print(f"          ✅ Content extracted from web: {len(content)} chars, lang: {language}")
                                else:
                                    print(f"          ⚠️  Web extraction returned empty")
                                
                            except Exception as e:
                                print(f"          ⚠️  Web extraction failed: {e}")
                            
                            # If web extraction failed, use RSS summary as fallback
                            if not content and entry.summary and len(entry.summary) > 100:
                                print(f"          📰 Using RSS summary as content ({len(entry.summary)} chars)")
                                content = entry.summary
                                language = 'en'  # Default to English for RSS summaries
                            
                            # If we have content (from web or RSS), process it
                            if content:
                                article.content_text = content
                                article.language = language
                                
                                # Store image URL in metadata
                                if image_url:
                                    print(f"          🖼️  Image found: {image_url[:60]}...")
                                    if article.article_metadata is None:
                                        article.article_metadata = {}
                                    article.article_metadata['image_url'] = image_url
                                elif not image_url:
                                    # Use EIA logo as fallback for EIA articles
                                    if 'eia.gov' in source.rss_url.lower():
                                        eia_logo = "/source-logos/eia.jpg"
                                        print(f"          🖼️  Using EIA logo as fallback")
                                        if article.article_metadata is None:
                                            article.article_metadata = {}
                                        article.article_metadata['image_url'] = eia_logo
                                
                                # Tag countries
                                country_codes, country_metadata = self.country_tagger.tag_article(
                                    article.title,
                                    content
                                )
                                if country_codes:
                                    print(f"          🌍 Countries tagged: {', '.join(country_codes)}")
                                    article.country_codes = country_codes
                                
                                # Tag topics
                                topic_tags = self.topic_tagger.tag_article(
                                    article.title,
                                    content
                                )
                                if topic_tags:
                                    print(f"          🏷️  Topics tagged: {', '.join(topic_tags)}")
                                    article.topic_tags = topic_tags
                                
                                # Store region metadata if present
                                if country_metadata:
                                    if article.article_metadata is None:
                                        article.article_metadata = {}
                                    article.article_metadata.update(country_metadata)
                            else:
                                stats.extraction_failed_count += 1
                                print(f"          ❌ No content available (web extraction and RSS summary both empty)")
                
                except Exception as e:
                    print(f"          ❌ Error processing entry: {e}")
                    stats.skipped_count += 1
                    continue
            
            # Commit after each source
            print(f"\n💾 Committing changes to database...")
            await self.db.commit()
            print(f"✅ Source '{source.name}' completed successfully\n")
            
        except FeedFetchError as e:
            print(f"❌ Feed fetch failed: {e}")
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": str(e),
            })
        
        except ValueError as e:
            print(f"❌ Parse error: {e}")
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": f"Parse error: {e}",
            })
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            stats.failed_sources.append({
                "source_id": source.id,
                "source_name": source.name,
                "error": f"Unexpected error: {e}",
            })
    
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
            print(f"\n🔍 Fetching enabled sources...")
            sources = await self.get_enabled_sources()
            print(f"✅ Found {len(sources)} enabled sources\n")
            
            if not sources:
                print("⚠️  No enabled sources found")
                run.status = "completed"
                run.finished_at = datetime.utcnow()
                run.stats = stats.to_dict()
                await self.db.commit()
                return run
            
            # Ingest each source
            for idx, source in enumerate(sources, 1):
                print(f"\n{'#'*60}")
                print(f"SOURCE {idx}/{len(sources)}")
                print(f"{'#'*60}")
                await self.ingest_source(source, stats)
            
            # Update run record
            run.status = "completed"
            run.finished_at = datetime.utcnow()
            run.stats = stats.to_dict()
            await self.db.commit()
            
            print(f"\n{'='*60}")
            print(f"INGESTION COMPLETE")
            print(f"{'='*60}")
            print(f"✨ New articles: {stats.new_count}")
            print(f"♻️  Updated articles: {stats.updated_count}")
            print(f"⏭️  Skipped: {stats.skipped_count}")
            print(f"❌ Extraction failures: {stats.extraction_failed_count}")
            print(f"⚠️  Failed sources: {len(stats.failed_sources)}")
            if stats.failed_sources:
                print(f"\nFailed sources:")
                for fs in stats.failed_sources:
                    print(f"  - {fs['source_name']}: {fs['error']}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.stats = stats.to_dict()
            run.stats["error"] = str(e)
            await self.db.commit()
            print(f"Ingestion failed: {e}")
            raise
        
        return run

"""
Vector search service for RAG.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import text

from app.db.models import ArticleChunk, Article
from app.services.rag.embedding_provider import EmbeddingProvider


class SearchFilters:
    """Filters for vector search."""
    
    def __init__(
        self,
        countries: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """
        Initialize search filters.
        
        Args:
            countries: List of ISO-3166 alpha-2 country codes
            topics: List of topic IDs
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
        """
        self.countries = countries
        self.topics = topics
        self.date_from = date_from
        self.date_to = date_to


class SearchResult:
    """Search result with chunk and article metadata."""
    
    def __init__(
        self,
        chunk_id: int,
        chunk_text: str,
        chunk_index: int,
        similarity: float,
        article_id: int,
        article_title: str,
        article_url: str,
        published_at: Optional[datetime],
        country_codes: Optional[List[str]],
        topic_tags: Optional[List[str]],
    ):
        """Initialize search result."""
        self.chunk_id = chunk_id
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.similarity = similarity
        self.article_id = article_id
        self.article_title = article_title
        self.article_url = article_url
        self.published_at = published_at
        self.country_codes = country_codes or []
        self.topic_tags = topic_tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "similarity": self.similarity,
            "article": {
                "id": self.article_id,
                "title": self.article_title,
                "url": self.article_url,
                "published_at": self.published_at.isoformat() if self.published_at else None,
                "country_codes": self.country_codes,
                "topic_tags": self.topic_tags,
            },
        }


class VectorSearchService:
    """
    Service for vector similarity search over article chunks.
    """
    
    def __init__(self, embedding_provider: EmbeddingProvider):
        """
        Initialize vector search service.
        
        Args:
            embedding_provider: Provider for generating query embeddings
        """
        self.embedding_provider = embedding_provider
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[SearchFilters] = None,
        k: int = 8,
    ) -> List[SearchResult]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            db: Database session
            query: Search query text
            filters: Optional filters for search
            k: Number of results to return
            
        Returns:
            List of search results ordered by similarity
        """
        # Generate query embedding
        query_embeddings = await self.embedding_provider.embed([query])
        query_embedding = query_embeddings[0]
        
        # Build filter conditions
        filter_conditions = []
        
        if filters:
            if filters.countries:
                # Match any of the specified countries
                filter_conditions.append(
                    ArticleChunk.country_codes.op("&&")(filters.countries)
                )
            
            if filters.topics:
                # Match any of the specified topics
                filter_conditions.append(
                    ArticleChunk.topic_tags.op("&&")(filters.topics)
                )
            
            if filters.date_from:
                filter_conditions.append(
                    ArticleChunk.published_at >= filters.date_from
                )
            
            if filters.date_to:
                filter_conditions.append(
                    ArticleChunk.published_at <= filters.date_to
                )
        
        # Build query with vector similarity
        # Using cosine distance (1 - cosine similarity)
        # Lower distance = higher similarity
        query_stmt = select(
            ArticleChunk.id,
            ArticleChunk.text,
            ArticleChunk.chunk_index,
            ArticleChunk.article_id,
            ArticleChunk.country_codes,
            ArticleChunk.topic_tags,
            ArticleChunk.published_at,
            Article.title,
            Article.url,
            ArticleChunk.embedding.cosine_distance(query_embedding).label("distance")
        ).join(
            Article, ArticleChunk.article_id == Article.id
        ).where(
            ArticleChunk.embedding.isnot(None)  # Only search chunks with embeddings
        )
        
        # Apply filters
        if filter_conditions:
            query_stmt = query_stmt.where(and_(*filter_conditions))
        
        # Order by similarity and limit
        query_stmt = query_stmt.order_by(text("distance")).limit(k)
        
        # Execute query
        result = await db.execute(query_stmt)
        rows = result.all()
        
        # Convert to SearchResult objects
        search_results = []
        for row in rows:
            # Convert distance to similarity (1 - distance for cosine)
            similarity = 1.0 - float(row.distance)
            
            search_results.append(SearchResult(
                chunk_id=row.id,
                chunk_text=row.text,
                chunk_index=row.chunk_index,
                similarity=similarity,
                article_id=row.article_id,
                article_title=row.title,
                article_url=row.url,
                published_at=row.published_at,
                country_codes=row.country_codes,
                topic_tags=row.topic_tags,
            ))
        
        return search_results
    
    async def search_with_threshold(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[SearchFilters] = None,
        k: int = 8,
        min_similarity: float = 0.5,
    ) -> List[SearchResult]:
        """
        Search with a minimum similarity threshold.
        
        Args:
            db: Database session
            query: Search query text
            filters: Optional filters
            k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of search results with similarity >= min_similarity
        """
        results = await self.search(db, query, filters, k)
        
        # Filter by minimum similarity
        return [r for r in results if r.similarity >= min_similarity]

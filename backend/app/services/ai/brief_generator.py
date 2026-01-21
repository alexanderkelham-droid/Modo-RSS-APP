"""
AI Brief Generation Service

Generates country-specific energy briefs from ingested articles.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article
from app.services.rag.chat_provider import ChatProvider


@dataclass
class BriefRequest:
    """Request for generating a brief."""
    country_code: Optional[str] = None
    topic: Optional[str] = None
    days: int = 7
    max_articles: int = 15


@dataclass
class BriefResponse:
    """Generated brief response."""
    brief: str
    article_count: int
    country_code: Optional[str]
    topic: Optional[str]
    date_range: dict


class BriefGenerator:
    """
    Service for generating AI briefs from articles.
    """
    
    def __init__(self, chat_provider: ChatProvider):
        """
        Initialize brief generator.
        
        Args:
            chat_provider: Provider for chat completions
        """
        self.chat_provider = chat_provider
    
    async def generate_brief(
        self,
        db: AsyncSession,
        request: BriefRequest,
    ) -> BriefResponse:
        """
        Generate a brief based on recent articles.
        
        Args:
            db: Database session
            request: Brief generation request
            
        Returns:
            Generated brief with metadata
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.days)
        
        # Fetch relevant articles
        articles = await self._fetch_articles(
            db=db,
            country_code=request.country_code,
            topic=request.topic,
            start_date=start_date,
            end_date=end_date,
            limit=request.max_articles,
        )
        
        if not articles:
            return BriefResponse(
                brief="No articles found matching the specified criteria.",
                article_count=0,
                country_code=request.country_code,
                topic=request.topic,
                date_range={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            )
        
        # Generate brief using AI
        brief = await self._generate_brief_text(
            articles=articles,
            country_code=request.country_code,
            topic=request.topic,
        )
        
        return BriefResponse(
            brief=brief,
            article_count=len(articles),
            country_code=request.country_code,
            topic=request.topic,
            date_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        )
    
    async def _fetch_articles(
        self,
        db: AsyncSession,
        country_code: Optional[str],
        topic: Optional[str],
        start_date: datetime,
        end_date: datetime,
        limit: int,
    ) -> List[Article]:
        """
        Fetch articles matching criteria.
        
        Args:
            db: Database session
            country_code: Country code filter (e.g., 'US', 'UK')
            topic: Topic filter
            start_date: Start date for articles
            end_date: End date for articles
            limit: Maximum number of articles
            
        Returns:
            List of matching articles
        """
        # Build query
        query = select(Article).where(
            and_(
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
        )
        
        # Apply country filter if specified
        if country_code:
            # Use PostgreSQL ANY operator for array matching
            query = query.where(
                Article.country_codes.any(country_code)
            )
        
        # Apply topic filter if specified
        if topic:
            # Use PostgreSQL ANY operator for array matching
            query = query.where(
                Article.topic_tags.any(topic)
            )
        
        # Order by date (newest first) and limit
        query = query.order_by(Article.published_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def _generate_brief_text(
        self,
        articles: List[Article],
        country_code: Optional[str],
        topic: Optional[str],
    ) -> str:
        """
        Generate brief text using AI.
        
        Args:
            articles: List of articles to summarize
            country_code: Country code for context
            topic: Topic for context
            
        Returns:
            Generated brief text
        """
        # Build context from articles
        article_summaries = []
        for i, article in enumerate(articles, start=1):
            # Use country_codes and topic_tags arrays directly
            countries = article.country_codes or []
            topics = article.topic_tags or []
            
            # Use content_text instead of content
            content_preview = (article.content_text[:500] if article.content_text else article.raw_summary[:500]) if (article.content_text or article.raw_summary) else "No content available"
            
            # Build article summary
            summary = f"""
[{i}] {article.title}
Published: {article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'}
Countries: {', '.join(countries) if countries else 'None'}
Topics: {', '.join(topics) if topics else 'None'}
URL: {article.url}

{content_preview}...
            """.strip()
            article_summaries.append(summary)
        
        context = "\n\n".join(article_summaries)
        
        # Build prompt
        filter_desc = []
        if country_code:
            filter_desc.append(f"country: {country_code}")
        if topic:
            filter_desc.append(f"topic: {topic}")
        
        filters_text = f" ({', '.join(filter_desc)})" if filter_desc else ""
        
        system_prompt = f"""You are an expert energy analyst writing a comprehensive brief on recent energy developments{filters_text}.

Your task is to analyze the provided articles and create a well-structured brief that:

1. **Overview**: Start with a 2-3 sentence executive summary of the key themes and developments
2. **Key Developments**: Highlight 3-5 major news items or trends, organized by importance
3. **Analysis**: Provide brief insights on what these developments mean for the energy sector
4. **Sources**: Reference specific articles using their numbers [1], [2], etc.

Guidelines:
- Write in a professional, analytical tone
- Focus on factual information from the articles
- Identify patterns and connections between different news items
- Be concise but comprehensive (aim for 400-600 words)
- Use clear section headings
- Cite sources frequently using [1], [2] format

Here are the articles to analyze:

{context}

Now write the brief:"""
        
        # Generate response using chat provider
        response = await self.chat_provider.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please generate the brief based on the articles provided."},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        
        return response

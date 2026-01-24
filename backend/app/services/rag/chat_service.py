"""
RAG chat service for answering questions using retrieved context.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag.vector_search import VectorSearchService, SearchFilters, SearchResult
from app.services.rag.chat_provider import ChatProvider
from app.services.rag.embedding_provider import EmbeddingProvider


@dataclass
class Citation:
    """Citation for a source article."""
    id: int
    title: str
    url: str
    published_at: Optional[datetime]
    source: str
    chunk_id: int
    similarity: float


@dataclass
class ChatResponse:
    """Response from chat service."""
    answer: str
    citations: List[Citation]
    confidence: str  # high, medium, low
    filters_applied: Dict[str, Any]


class ChatService:
    """
    Service for RAG-based question answering.
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        chat_provider: ChatProvider,
        min_similarity_threshold: float = 0.5,
        low_confidence_threshold: float = 0.65,
    ):
        """
        Initialize chat service.
        
        Args:
            embedding_provider: Provider for query embeddings
            chat_provider: Provider for chat completions
            min_similarity_threshold: Minimum similarity to consider a chunk relevant
            low_confidence_threshold: Threshold for low confidence warning
        """
        self.embedding_provider = embedding_provider
        self.chat_provider = chat_provider
        self.vector_search = VectorSearchService(embedding_provider)
        self.min_similarity_threshold = min_similarity_threshold
        self.low_confidence_threshold = low_confidence_threshold
    
    def _build_system_prompt(self, chunks: List[SearchResult]) -> str:
        """
        Build system prompt with context and instructions.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            System prompt text
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] {chunk.chunk_text}\n"
                f"(Source: {chunk.article_title}, Published: {chunk.published_at.strftime('%Y-%m-%d') if chunk.published_at else 'Unknown'})"
            )
        
        context = "\n\n".join(context_parts)
        
        # Build system prompt
        system_prompt = f"""You are an AI assistant specialized in energy transition news and policy.

Your task is to answer questions using ONLY the context provided below. Follow these rules strictly:

1. Base your answer ONLY on the provided context
2. Cite sources using bracketed numbers like [1], [2], etc. corresponding to the context items
3. If the context doesn't contain enough information to answer the question fully, say so explicitly
4. Do not use external knowledge or make assumptions beyond what's in the context
5. Be concise but comprehensive in your answer
6. Use multiple citations if relevant information comes from multiple sources

Context:
{context}

Now answer the user's question using only the context above."""
        
        return system_prompt
    
    def _extract_citations(
        self,
        chunks: List[SearchResult],
    ) -> List[Citation]:
        """
        Extract unique article citations from chunks.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            List of unique citations
        """
        # Track unique articles (deduplicate by article_id)
        seen_articles = set()
        citations = []
        
        for chunk in chunks:
            if chunk.article_id not in seen_articles:
                citations.append(Citation(
                    id=chunk.article_id,
                    title=chunk.article_title,
                    url=chunk.article_url,
                    published_at=chunk.published_at,
                    source=chunk.article_url.split('/')[2] if '://' in chunk.article_url else 'Unknown',  # Extract domain
                    chunk_id=chunk.chunk_id,
                    similarity=chunk.similarity,
                ))
                seen_articles.add(chunk.article_id)
        
        return citations
    
    def _assess_confidence(self, chunks: List[SearchResult]) -> str:
        """
        Assess confidence level based on retrieval quality.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        if not chunks:
            return "low"
        
        max_similarity = max(c.similarity for c in chunks)
        avg_similarity = sum(c.similarity for c in chunks) / len(chunks)
        
        if max_similarity >= 0.8 and avg_similarity >= 0.7:
            return "high"
        elif max_similarity >= self.low_confidence_threshold:
            return "medium"
        else:
            return "low"
    
    async def chat(
        self,
        db: AsyncSession,
        question: str,
        filters: Optional[SearchFilters] = None,
        k: int = 8,
    ) -> ChatResponse:
        """
        Answer a question using RAG.
        
        Args:
            db: Database session
            question: User question
            filters: Optional search filters
            k: Number of chunks to retrieve
            
        Returns:
            ChatResponse with answer and citations
        """
        # Retrieve relevant chunks
        chunks = await self.vector_search.search_with_threshold(
            db=db,
            query=question,
            filters=filters,
            k=k,
            min_similarity=self.min_similarity_threshold,
        )
        
        # Assess confidence
        confidence = self._assess_confidence(chunks)
        
        # Handle low confidence case - use general LLM knowledge
        if not chunks or confidence == "low":
            # Use general knowledge system prompt
            general_prompt = """You are an AI assistant specializing in energy and renewable energy topics.
            
The user has asked a question, but we don't have relevant articles in our database to answer it directly.
However, you can use your general knowledge to provide a helpful answer.

IMPORTANT: At the end of your response, add a note that this answer is based on general knowledge 
since we don't have specific articles on this topic in our database.

Be helpful, accurate, and concise."""
            
            messages = [
                {"role": "system", "content": general_prompt},
                {"role": "user", "content": question},
            ]
            
            answer = await self.chat_provider.generate(
                messages=messages,
                temperature=0.3,  # Slightly higher for general knowledge
                max_tokens=1000,
            )
            
            return ChatResponse(
                answer=answer,
                citations=[],
                confidence="low",
                filters_applied=self._serialize_filters(filters),
            )
        
        # Build prompt with context
        system_prompt = self._build_system_prompt(chunks)
        
        # Generate answer
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        
        answer = await self.chat_provider.generate(
            messages=messages,
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1000,
        )
        
        # Extract citations
        citations = self._extract_citations(chunks)
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            filters_applied=self._serialize_filters(filters),
        )
    
    def _serialize_filters(self, filters: Optional[SearchFilters]) -> Dict[str, Any]:
        """Serialize filters for response."""
        if not filters:
            return {}
        
        result = {}
        if filters.countries:
            result["countries"] = filters.countries
        if filters.topics:
            result["topics"] = filters.topics
        if filters.date_from:
            result["date_from"] = filters.date_from.isoformat()
        if filters.date_to:
            result["date_to"] = filters.date_to.isoformat()
        
        return result

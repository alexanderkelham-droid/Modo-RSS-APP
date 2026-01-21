"""
Chat API endpoints for RAG-based question answering.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat import ChatRequest, ChatResponseModel, CitationResponse
from app.services.rag.chat_service import ChatService, SearchFilters
from app.services.rag.chat_provider import OpenAIChatProvider
from app.services.rag.embedding_provider import OpenAIEmbeddingProvider
from app.settings import settings

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency to get chat service."""
    embedding_provider = OpenAIEmbeddingProvider(
        api_key=settings.OPENAI_API_KEY,
        dimension=1536,
    )
    chat_provider = OpenAIChatProvider(
        api_key=settings.OPENAI_API_KEY,
    )
    return ChatService(
        embedding_provider=embedding_provider,
        chat_provider=chat_provider,
        min_similarity_threshold=0.5,
        low_confidence_threshold=0.65,
    )


@router.post("", response_model=ChatResponseModel)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Answer a question using RAG over ingested articles.
    
    The system will:
    1. Retrieve relevant article chunks using vector search
    2. Apply optional filters (countries, topics, date range)
    3. Generate an answer using only the retrieved context
    4. Return answer with citations to source articles
    5. Indicate confidence level based on retrieval quality
    
    If retrieval confidence is low, the system will suggest adjusting filters.
    """
    try:
        # Convert filters
        filters = None
        if request.filters:
            filters = SearchFilters(
                countries=request.filters.countries,
                topics=request.filters.topics,
                date_from=request.filters.date_from,
                date_to=request.filters.date_to,
            )
        
        # Generate response
        response = await chat_service.chat(
            db=db,
            question=request.question,
            filters=filters,
            k=request.k,
        )
        
        # Convert to API response
        return ChatResponseModel(
            answer=response.answer,
            citations=[
                CitationResponse(
                    id=c.id,
                    title=c.title,
                    url=c.url,
                    published_at=c.published_at,
                    source=c.source,
                    chunk_id=c.chunk_id,
                    similarity=c.similarity,
                )
                for c in response.citations
            ],
            confidence=response.confidence,
            filters_applied=response.filters_applied,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
FastAPI application entry point for ETI backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ingestion, chat, articles, countries, sources, briefs, stats

app = FastAPI(
    title="Energy Transition Intelligence API",
    description="RSS aggregation and RAG chatbot for energy transition news",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(ingestion.router)
app.include_router(chat.router)
app.include_router(articles.router)
app.include_router(countries.router)
app.include_router(sources.router)
app.include_router(briefs.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ETI API"}


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

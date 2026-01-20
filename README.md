# Energy Transition Intelligence (ETI)

A web application that aggregates energy transition news via RSS feeds, enriches it with country and topic tagging, and provides a RAG-powered chatbot for intelligent Q&A over the corpus.

## Features

- 📰 **RSS Ingestion**: Automated fetching and parsing of energy news from configured sources
- 🌍 **Smart Enrichment**: Automatic country (ISO-3166) and topic classification
- 🔍 **Vector Search**: pgvector-powered semantic search over article chunks
- 💬 **RAG Chatbot**: Context-grounded answers with citations and confidence-based abstention
- 📊 **Dashboard**: Filterable news view by country, topic, and date range

## Tech Stack

- **Backend**: FastAPI (Python) with async SQLAlchemy
- **Database**: PostgreSQL + pgvector
- **Embeddings**: Abstracted provider interface (OpenAI/local/test)
- **Frontend**: TBD (Next.js or Streamlit)

## Project Structure

```
backend/
  api/          # FastAPI routes
  db/           # Database models & connections
  models/       # Pydantic schemas
  services/
    ingest/     # RSS parsing & extraction
    nlp/        # Enrichment (language, country, topics)
    rag/        # Vector search & chat
  tests/        # Unit & integration tests
frontend/       # TBD
```

## Setup

(Coming soon)

## Development Status

🚧 **In Active Development** - MVP Phase

---

Built for the energy transition community 🌱

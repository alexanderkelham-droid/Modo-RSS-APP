# Energy Transition Intelligence (ETI)

A complete news aggregation and analysis platform for the energy transition sector. Ingests RSS feeds, enriches content with AI-powered tagging, provides vector search, and offers a RAG chatbot with citations.

## 🎯 Features

- 📰 **Automated RSS Ingestion**: 30-minute scheduled fetching from multiple sources
- 🌍 **Smart Enrichment**: 
  - 50+ country detection (ISO-3166 codes)
  - 11 energy transition topic classification
  - Language detection
  - Full-text extraction (readability-lxml)
- 🔍 **Vector Search**: pgvector with OpenAI embeddings (text-embedding-3-small)
- 💬 **RAG Chatbot**: 
  - Context-grounded answers with citations
  - Confidence-based abstention
  - Filter by country, topic, date
- 📊 **Dashboard**: 
  - Top stories ranking (recency + source tier + keywords)
  - Country sidebar with counts
  - Topic and date filters
  - Real-time chat panel
- 🔄 **Background Worker**: APScheduler running every 30 minutes

## 🏗️ Tech Stack

- **Backend**: FastAPI (Python 3.11+) with async SQLAlchemy 2.0
- **Database**: Supabase (PostgreSQL 16 + pgvector)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Chat**: OpenAI gpt-4o-mini
- **Frontend**: Next.js 14 with Tailwind CSS & SWR
- **Scheduler**: APScheduler
- **Deployment**: Docker Compose

## ⚠️ SETUP REQUIRED BEFORE TESTING

### 1. Get Your Supabase Database Password

**Go to**: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/settings/database

- Copy your database password (or reset it)
- Edit `.env` file
- Replace `[YOUR-DB-PASSWORD]` with your actual password

### 2. Enable pgvector Extension

**Go to**: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/database/extensions

- Search for "vector"
- Click to enable the `vector` extension

### 3. Run Database Migrations

```powershell
# Temporarily change .env DATABASE_URL to direct connection (port 5432)
# From: ...pooler.supabase.com:6543...?pgbouncer=true
# To:   ...db.tujrzlxbckqyuwqrylck.supabase.co:5432...

cd backend
poetry install
poetry run alembic upgrade head
cd ..

# Change .env back to pooler connection
```

## 🚀 Quick Start

```powershell
# Start all services
docker compose up -d

# Check status
docker compose ps

# Create your first source
$body = @{
    name = "Reuters Energy"
    rss_url = "https://www.reuters.com/technology/energy/"
    enabled = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/sources -Method POST -Body $body -ContentType "application/json"

# Run manual ingestion
docker compose exec backend python -m app.ingest.run_once

# Open frontend
Start-Process http://localhost:3000
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup guide
- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Supabase configuration details
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Comprehensive testing plan
- **[PROCESS_LOG.md](PROCESS_LOG.md)** - Development session log
- **[backend/INGESTION_WORKER.md](backend/INGESTION_WORKER.md)** - Worker documentation

## 🔧 Project Structure

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

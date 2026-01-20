# ETI Project Process Log

This document tracks all development steps, decisions, and progress for the Energy Transition Intelligence (ETI) project.

---

## 2026-01-20 | Session 1: Project Initialization & Planning

### Task
Initial project briefing and setup of process logging system.

### Accomplishments
- **Project scope defined**: RSS news aggregation + enrichment + RAG chatbot for energy transition domain
- **Core features identified**:
  - RSS ingestion pipeline with deduplication
  - Content extraction from article URLs
  - Enrichment (language, country ISO-3166-alpha-2, 11 topic tags)
  - Chunking + vector embeddings (800-1200 chars)
  - Dashboard with filters
  - RAG chatbot with citations and abstention logic
  
- **Technical stack confirmed**:
  - Backend: FastAPI (Python) + async SQLAlchemy
  - Database: Postgres + pgvector
  - Abstracted LLM/embedding providers (swappable)
  - Clean folder structure: `api/`, `db/`, `models/`, `services/ingest/`, `services/nlp/`, `services/rag/`
  - Testing: Unit + integration with mocks

- **MVP boundaries set**:
  - ✅ RSS-only sources (no paywall handling)
  - ✅ Best-effort extraction
  - ❌ Story clustering (v2 feature)
  - ❌ Full robots.txt compliance

### Key Decisions
- Process log established as `PROCESS_LOG.md` in project root
- Log will be updated after each coding session

### Next Steps
- Design folder structure
- Define database schema
- List initial dependencies

---


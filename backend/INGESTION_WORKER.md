# ETI Ingestion Worker

## Overview

Background scheduler for automated news ingestion using APScheduler.

## Components

### 1. Pipeline (`app/ingest/pipeline.py`)
Complete ingestion pipeline with 6 steps:
1. Fetch RSS feeds
2. Parse articles
3. Extract content (readability)
4. Tag countries and topics
5. Chunk articles (800-1200 chars)
6. Generate embeddings (OpenAI)

Returns structured metrics with error tracking.

### 2. Worker (`app/ingest/worker.py`)
Background process that runs pipeline every 30 minutes.

**Run with:**
```bash
python -m app.ingest.worker
```

**Features:**
- Runs immediately on startup
- 30-minute interval schedule
- Prevents overlapping runs (max_instances=1)
- Comprehensive logging to console + file
- Graceful shutdown on Ctrl+C

### 3. CLI Command (`app/ingest/run_once.py`)
Manual ingestion trigger for testing/debugging.

**Run with:**
```bash
python -m app.ingest.run_once
```

**Features:**
- One-time execution
- Detailed metrics logging
- Exit code 1 if errors occurred

## Docker Setup

The worker runs as a separate service in docker-compose.yml:

```yaml
worker:
  build: ./backend
  command: python -m app.ingest.worker
  depends_on:
    - postgres
    - backend
  volumes:
    - ./logs:/app/logs
```

## Makefile Commands

```bash
# View worker logs
make logs-worker

# Trigger manual ingestion
make ingest-now
```

## Metrics

Each ingestion run tracks:
- `sources_processed`: Number of RSS sources fetched
- `articles_fetched`: Total articles from RSS feeds
- `articles_new`: New articles created
- `articles_updated`: Existing articles updated
- `articles_extracted`: Articles with content extracted
- `articles_tagged`: Articles with country/topic tags
- `chunks_created`: Text chunks created
- `chunks_embedded`: Embeddings generated
- `errors`: Number of errors (with details)
- `duration_seconds`: Total execution time

## Logging

**Format:**
```
2026-01-20 10:00:00 - app.ingest.pipeline - INFO - Starting full ingestion pipeline
2026-01-20 10:00:05 - app.ingest.pipeline - INFO - Processing source: Reuters Energy
2026-01-20 10:00:10 - app.ingest.pipeline - INFO -   Fetched 15 articles
2026-01-20 10:01:30 - app.ingest.pipeline - INFO - Ingestion completed in 90.2s: 3 sources, 10 new articles, 45 chunks, 45 embeddings, 0 errors
```

**Log files:**
- `logs/ingestion_worker.log` - Worker process logs (append mode)

## Error Handling

- **Network errors**: Logged, source skipped, pipeline continues
- **Extraction failures**: Logged, article skipped (no content)
- **Embedding failures**: Logged, chunks saved without embeddings
- **Tagging failures**: Logged, article saved without tags
- **Partial failures**: Pipeline completes with error count

## Testing

Run pipeline tests:
```bash
pytest tests/test_pipeline.py -v
```

Tests cover:
- Metrics tracking
- Empty database handling
- Full pipeline execution
- Error handling and recovery
- Skipping existing articles
- Embedding failure graceful degradation

## Production Considerations

1. **API Rate Limits**: OpenAI embedding API has rate limits
   - Current: Batch processing per article
   - Future: Global rate limiter with retry logic

2. **Long-running Sources**: Some RSS feeds may be slow
   - Current: 30-minute interval allows time to complete
   - Future: Per-source timeout configuration

3. **Database Connections**: Pipeline uses connection pooling
   - Async session maker handles connection lifecycle
   - Auto-commit on success, rollback on error

4. **Monitoring**: 
   - Check worker logs for errors
   - Track metrics over time for trends
   - Alert on high error rates

5. **Scaling**:
   - Current: Single worker process
   - Future: Multiple workers with distributed task queue (Celery)

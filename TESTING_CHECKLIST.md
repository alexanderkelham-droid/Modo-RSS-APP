# ETI Testing Checklist

## Prerequisites Setup

### 1. Get Supabase Database Password
- [ ] Go to https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/settings/database
- [ ] Copy or reset your database password
- [ ] Update `.env` file with the password (replace `[YOUR-DB-PASSWORD]`)

### 2. Enable pgvector Extension
- [ ] Go to https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/database/extensions
- [ ] Search for "vector"
- [ ] Click "Enable" on the `vector` extension

### 3. Verify Environment Variables
- [ ] Check `.env` file has:
  - `OPENAI_API_KEY` ✓ (already set)
  - `DATABASE_URL` with your Supabase password
  - `SUPABASE_URL` ✓ (already set)
  - `SUPABASE_KEY` ✓ (already set)

## Testing Steps

### Phase 1: Database Connection

```bash
# Test database connection with Python
docker compose run --rm backend python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+asyncpg://')); print('Connection successful!')"
```

Expected: "Connection successful!"

### Phase 2: Run Migrations

```bash
# For migrations, temporarily use direct connection (port 5432) in .env
# Change: ...pooler.supabase.com:6543... to ...db.tujrzlxbckqyuwqrylck.supabase.co:5432...
# Remove: ?pgbouncer=true

# Run migrations
docker compose run --rm backend alembic upgrade head

# Change back to pooler connection after migrations complete
```

Expected: No errors, tables created in Supabase

### Phase 3: Start Services

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

Expected: All services running (backend, worker, frontend, redis)

### Phase 4: Backend API Tests

```bash
# Run pytest
docker compose exec backend pytest tests/ -v

# Or run specific test files
docker compose exec backend pytest tests/test_country_tagger.py -v
docker compose exec backend pytest tests/test_topic_tagger.py -v
docker compose exec backend pytest tests/test_embedding_provider.py -v
```

Expected: All tests passing (might skip OpenAI tests if using fake providers)

### Phase 5: API Endpoint Tests

```powershell
# Health check
Invoke-WebRequest http://localhost:8000/docs

# Countries endpoint
Invoke-WebRequest http://localhost:8000/countries

# Sources endpoint
Invoke-WebRequest http://localhost:8000/sources
```

Expected: 200 responses, JSON data

### Phase 6: Create Test Source

```powershell
# Create a test RSS source
$body = @{
    name = "Reuters Energy"
    rss_url = "https://www.reuters.com/rssFeed/businessNews"
    enabled = $true
    type = "rss"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/sources -Method POST -Body $body -ContentType "application/json"
```

Expected: 201 Created, source JSON returned

### Phase 7: Manual Ingestion Test

```bash
# Trigger one-time ingestion
docker compose exec backend python -m app.ingest.run_once

# Check logs
docker compose logs worker
```

Expected: Articles fetched, content extracted, chunks created, embeddings generated

### Phase 8: Check Database

```bash
# Connect to Supabase database via SQL Editor
# Go to: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/editor

# Run queries:
SELECT COUNT(*) FROM sources;
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM article_chunks;

# Check vector embeddings
SELECT id, title, chunk_index FROM article_chunks LIMIT 5;
```

Expected: Data populated in all tables

### Phase 9: Test Chat Endpoint

```powershell
# Test chat with question
$chatBody = @{
    question = "What are the latest developments in solar energy?"
    filters = @{
        topics = @("renewables_solar")
    }
    k = 5
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/chat -Method POST -Body $chatBody -ContentType "application/json"
```

Expected: Answer with citations

### Phase 10: Frontend Test

```bash
# Start frontend (if not already running)
cd frontend
npm install
npm run dev

# Or with Docker
docker compose up frontend
```

Open http://localhost:3000

Expected: Dashboard loads, can select countries, see stories, chat works

## Troubleshooting

### Database Connection Issues
- Verify password in `.env` is correct
- Check Supabase project is not paused
- Ensure pgvector extension is enabled
- Try direct connection (port 5432) vs pooler (port 6543)

### Migration Errors
- Use direct connection (port 5432) for migrations
- Check pgvector extension is enabled first
- Look for SQL syntax errors in migration files

### OpenAI API Errors
- Verify API key is valid: https://platform.openai.com/api-keys
- Check quota/billing: https://platform.openai.com/usage
- Test with fake providers first (no API calls)

### Ingestion Errors
- Check RSS URLs are valid
- Verify network connectivity
- Look at worker logs: `docker compose logs worker`
- Test individual services (fetcher, parser, extractor)

### Frontend Issues
- Check API URL in frontend/.env.local
- Verify CORS is enabled in backend
- Check browser console for errors
- Test API endpoints directly first

## Success Criteria

✅ All migrations run successfully  
✅ Backend tests pass (at least 100+ tests)  
✅ Can create sources via API  
✅ Manual ingestion completes without errors  
✅ Articles, chunks, and embeddings created  
✅ Chat endpoint returns answers with citations  
✅ Frontend loads and displays data  
✅ Worker scheduler runs every 30 minutes  

## Next Steps After Testing

1. Add seed data (realistic RSS sources)
2. Monitor worker logs for issues
3. Set up error alerts
4. Configure Row Level Security in Supabase
5. Optimize vector search indexes
6. Add more comprehensive tests

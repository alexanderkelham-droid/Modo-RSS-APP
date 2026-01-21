# Quick Start Guide

## Step 1: Get Your Supabase Database Password

**You need to get your database password from Supabase:**

1. Open this URL in your browser:
   ```
   https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/settings/database
   ```

2. Scroll down to find your database password
   - If you see it, copy it
   - If you don't see it, click "Reset Database Password" and copy the new one

3. Update the `.env` file:
   - Open `.env` in this directory
   - Find the line: `DATABASE_URL=postgresql://postgres.tujrzlxbckqyuwqrylck:[YOUR-DB-PASSWORD]@...`
   - Replace `[YOUR-DB-PASSWORD]` with your actual password

## Step 2: Enable pgvector Extension

1. Go to: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/database/extensions

2. Search for "vector" in the extensions list

3. Click the toggle to "Enable" the `vector` extension

## Step 3: Test the Setup

Open PowerShell in this directory and run:

```powershell
# Check environment variables
Get-Content .env | Select-String -Pattern "OPENAI_API_KEY|DATABASE_URL"

# Verify OPENAI_API_KEY is set (should see the sk-proj-... key)
# Verify DATABASE_URL has your password (not [YOUR-DB-PASSWORD])
```

## Step 4: Run Database Migrations

**Important:** For migrations, you need to use the DIRECT connection (port 5432), not the pooler.

1. Temporarily edit `.env` and change the DATABASE_URL:
   ```
   # Change FROM (pooler):
   DATABASE_URL=postgresql://postgres.tujrzlxbckqyuwqrylck:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
   
   # Change TO (direct):
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.tujrzlxbckqyuwqrylck.supabase.co:5432/postgres
   ```

2. Run migrations:
   ```powershell
   # Install Python dependencies first
   cd backend
   poetry install
   
   # Run migrations
   poetry run alembic upgrade head
   
   cd ..
   ```

3. After migrations complete, change `.env` back to the pooler connection

## Step 5: Start the Services

```powershell
# Start services with Docker
docker compose up -d

# Check status
docker compose ps

# Should see: backend, worker, frontend, redis all running
```

## Step 6: Test the API

Open in browser:
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

Or test with PowerShell:
```powershell
# Test health
Invoke-WebRequest http://localhost:8000/countries | Select-Object -Property StatusCode

# Should return: StatusCode: 200
```

## Step 7: Create Your First Source

```powershell
$body = @{
    name = "Reuters Energy"
    rss_url = "https://www.reuters.com/technology/energy/"
    enabled = $true
    type = "rss"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/sources -Method POST -Body $body -ContentType "application/json"
```

## Step 8: Run Manual Ingestion

```powershell
# Trigger ingestion
docker compose exec backend python -m app.ingest.run_once

# Watch the logs
docker compose logs -f worker
```

## Troubleshooting

### "Cannot connect to database"
- Make sure you replaced `[YOUR-DB-PASSWORD]` in `.env` with your actual password
- Check Supabase project isn't paused
- Try the direct connection (port 5432) instead of pooler (port 6543)

### "pgvector extension not found"
- Enable the vector extension in Supabase dashboard (Step 2 above)
- Run migrations again

### "Poetry not found"
Install Poetry:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Or use pip:
```powershell
pip install poetry
```

### Docker issues
Make sure Docker Desktop is running:
```powershell
docker --version
docker compose version
```

## What to Expect

✅ Migrations create tables: sources, articles, article_chunks, ingestion_runs  
✅ Backend API runs on http://localhost:8000  
✅ Frontend dashboard runs on http://localhost:3000  
✅ Worker runs ingestion every 30 minutes  
✅ Test ingestion fetches articles, extracts content, creates embeddings  

## Next Steps

Once everything is running:
1. Check [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for comprehensive testing
2. Add more RSS sources via the API
3. Test the chat endpoint with questions
4. Explore the frontend dashboard

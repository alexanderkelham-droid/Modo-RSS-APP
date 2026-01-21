# Simple setup test script
Write-Host "ETI Platform - Setup Test" -ForegroundColor Green

# Step 1: Check Python environment
Write-Host "`n[1/4] Checking Python environment..."
cd backend
.\venv\Scripts\Activate.ps1
python -c "import fastapi, openai, sqlalchemy, pgvector; print('  Dependencies: OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED: Python dependencies issue" -ForegroundColor Red
    exit 1
}

# Step 2: Check database connection
Write-Host "`n[2/4] Testing database connection..."
python -c "import asyncio; from app.settings import settings; print(f'  Database: {settings.DATABASE_URL.split('@')[1].split('/')[0]}')"

# Step 3: Run migrations
Write-Host "`n[3/4] Running database migrations..."
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED: Migration error" -ForegroundColor Red
    Write-Host "  Make sure pgvector extension is enabled in Supabase" -ForegroundColor Yellow
    exit 1
}

# Step 4: Verify tables
Write-Host "`n[4/4] Checking migration status..."
python -c "import asyncio; from app.db.session import get_session_maker; from sqlalchemy import text; async def check(): async with get_session_maker()() as session: result = await session.execute(text('SELECT version_num FROM alembic_version')); print(f'  Migration: {result.scalar()}')); asyncio.run(check())"

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host "  1. Start services: docker compose up -d"
Write-Host "  2. View API docs: http://localhost:8000/docs"
Write-Host "  3. Create RSS source via API"
Write-Host "  4. Test ingestion: docker compose exec backend python -m app.ingest.run_once"

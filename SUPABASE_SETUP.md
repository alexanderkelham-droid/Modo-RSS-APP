# Supabase Setup Guide

## Getting Your Database Password

1. Go to: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/settings/database
2. Look for "Database Password" section
3. Copy your password (or reset it if you don't have it)

## Update Environment Variables

Edit `.env` file and replace `[YOUR-DB-PASSWORD]` with your actual password:

```bash
# Connection pooler (use this for the app - port 6543)
DATABASE_URL=postgresql://postgres.tujrzlxbckqyuwqrylck:YOUR_PASSWORD_HERE@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# Direct connection (use this for migrations - port 5432)
# Uncomment and use when running migrations
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@db.tujrzlxbckqyuwqrylck.supabase.co:5432/postgres
```

## Enable pgvector Extension

1. Go to: https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/database/extensions
2. Search for "vector"
3. Enable the `vector` extension

## Run Migrations

Once you have the password configured:

```bash
# For local development (direct connection)
# First, temporarily change DATABASE_URL in .env to the direct connection (port 5432)
alembic upgrade head

# Or with Docker
docker compose run --rm backend alembic upgrade head
```

## Connection Strings Explained

**Pooler Connection (Port 6543)** - Use for application:
- Uses PgBouncer connection pooling
- Better for multiple connections
- Default for FastAPI app
- Format: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true`

**Direct Connection (Port 5432)** - Use for migrations:
- Direct connection to PostgreSQL
- Required for schema changes (Alembic migrations)
- Format: `postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres`

## Project Details

- **Project Ref**: tujrzlxbckqyuwqrylck
- **API URL**: https://tujrzlxbckqyuwqrylck.supabase.co
- **Region**: US East (AWS)
- **Database Host**: db.tujrzlxbckqyuwqrylck.supabase.co
- **Pooler Host**: aws-0-us-east-1.pooler.supabase.com

## Testing Connection

```bash
# Test with psql (if installed)
psql "postgresql://postgres:YOUR_PASSWORD@db.tujrzlxbckqyuwqrylck.supabase.co:5432/postgres"

# Or test from Python
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); print(engine.connect())"
```

"""Enable pgvector extension in Supabase."""
import asyncio
import asyncpg
from app.settings import settings

async def enable_pgvector():
    """Enable pgvector extension."""
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(url)
        print("Enabling pgvector extension...")
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        print("✅ pgvector extension enabled")
        
        # Verify tables exist
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        print(f"\n✅ Tables created: {', '.join([t['tablename'] for t in tables])}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(enable_pgvector())
    exit(0 if success else 1)

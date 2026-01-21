"""Test database connection with different configurations."""
import asyncio
import asyncpg
from app.settings import settings

async def test_connection():
    """Test asyncpg connection to Supabase."""
    print(f"Testing connection to: {settings.DATABASE_URL[:50]}...")
    
    # Parse URL to get components
    url = settings.DATABASE_URL
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Parsed URL: {url[:60]}...")
    
    try:
        conn = await asyncpg.connect(url)
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL version: {version[:80]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)

"""Rename metadata column to article_metadata."""
import asyncio
import asyncpg

async def rename_column():
    conn = await asyncpg.connect('postgresql://postgres.tujrzlxbckqyuwqrylck:Basiaks%2123456@aws-1-eu-west-1.pooler.supabase.com:5432/postgres')
    try:
        await conn.execute('ALTER TABLE articles RENAME COLUMN metadata TO article_metadata;')
        print('✅ Column renamed: metadata → article_metadata')
    except Exception as e:
        print(f'Column might already be renamed or error: {e}')
    finally:
        await conn.close()

asyncio.run(rename_column())

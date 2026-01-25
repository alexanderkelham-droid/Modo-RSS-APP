"""
Test NESO ingestion only.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal
from app.db.models import Source
from app.ingest.pipeline import run_full_ingestion_pipeline


async def test_neso_only():
    """Disable all sources except NESO, run pipeline, then re-enable."""
    async with AsyncSessionLocal() as db:
        # Disable all sources except NESO
        await db.execute(
            update(Source).where(Source.name != "NESO").values(enabled=False)
        )
        await db.commit()
    
    print("🚀 Running pipeline for NESO only...\n")
    
    try:
        metrics = await run_full_ingestion_pipeline()
        
        print("\n✅ Pipeline completed!")
        print(f"\n📊 Metrics:")
        print(f"   Sources processed: {metrics.get('sources_processed')}")
        print(f"   Articles fetched: {metrics.get('articles_fetched')}")
        print(f"   Articles new: {metrics.get('articles_new')}")
        print(f"   Articles extracted: {metrics.get('articles_extracted')}")
        print(f"   Articles tagged: {metrics.get('articles_tagged')}")
        print(f"   Chunks created: {metrics.get('chunks_created')}")
        print(f"   Embeddings generated: {metrics.get('embeddings_generated')}")
    
    finally:
        # Re-enable all sources
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Source).values(enabled=True)
            )
            await db.commit()
        print("\n✅ Re-enabled all sources")


if __name__ == "__main__":
    asyncio.run(test_neso_only())

"""
Test running the ingestion pipeline with NESO.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ingest.pipeline import run_full_ingestion_pipeline


async def test_pipeline():
    """Test the ingestion pipeline."""
    print("🚀 Starting ingestion pipeline...\n")
    
    metrics = await run_full_ingestion_pipeline()
    
    print("\n✅ Pipeline completed!")
    print(f"\n📊 Metrics:")
    print(f"   Sources processed: {metrics.get('sources_processed')}")
    print(f"   Articles fetched: {metrics.get('articles_fetched')}")
    print(f"   Articles new: {metrics.get('articles_new')}")
    print(f"   Articles updated: {metrics.get('articles_updated')}")
    print(f"   Articles extracted: {metrics.get('articles_extracted')}")
    print(f"   Articles tagged (countries): {metrics.get('articles_tagged_countries')}")
    print(f"   Articles tagged (topics): {metrics.get('articles_tagged_topics')}")
    print(f"   Chunks created: {metrics.get('chunks_created')}")
    print(f"   Embeddings generated: {metrics.get('embeddings_generated')}")
    
    if metrics.get('errors'):
        print(f"\n❌ Errors ({len(metrics['errors'])}):")
        for error in metrics['errors'][:5]:  # Show first 5 errors
            print(f"   - {error}")


if __name__ == "__main__":
    asyncio.run(test_pipeline())

"""
One-time setup script for Railway deployment.
Adds NESO source and runs initial pipeline ingestion.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.database import get_sync_db
from app.models import Source
from app.ingest.pipeline import run_full_ingestion_pipeline


def add_neso_source():
    """Add NESO source if it doesn't exist."""
    db = next(get_sync_db())
    
    try:
        # Check if NESO source already exists
        existing = db.query(Source).filter(Source.name == "NESO").first()
        
        if existing:
            print(f"✅ NESO source already exists (ID: {existing.id})")
            return existing
        
        # Create new NESO source
        neso_source = Source(
            name="NESO",
            type="web_scraper",
            rss_url="neso",  # This is the scraper name in the registry
            enabled=True,
        )
        
        db.add(neso_source)
        db.commit()
        db.refresh(neso_source)
        
        print(f"✅ Created NESO source (ID: {neso_source.id})")
        return neso_source
        
    except Exception as e:
        print(f"❌ Error adding NESO source: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def main():
    """Add NESO source and run pipeline."""
    print("=" * 80)
    print("Railway Setup - NESO Integration")
    print("=" * 80)
    
    # Step 1: Add NESO source
    print("\n📝 Step 1: Adding NESO source to database...")
    neso_source = add_neso_source()
    
    # Step 2: Run pipeline
    print("\n📝 Step 2: Running ingestion pipeline...")
    await run_full_ingestion_pipeline()
    
    print("\n" + "=" * 80)
    print("✅ Setup complete! NESO articles should now be available.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

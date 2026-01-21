"""
CLI command for running ingestion once manually.

Run with: python -m app.ingest.run_once
"""

import logging
import asyncio
import sys
from datetime import datetime

from app.ingest.pipeline import run_full_ingestion_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run ingestion pipeline once."""
    logger.info("=" * 80)
    logger.info(f"Manual ingestion run started at {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)
    
    try:
        metrics = await run_full_ingestion_pipeline()
        
        logger.info("=" * 80)
        logger.info("Manual ingestion completed successfully!")
        logger.info("=" * 80)
        logger.info("Summary:")
        for key, value in metrics.items():
            if key != 'error_details':  # Skip detailed errors in summary
                logger.info(f"  {key}: {value}")
        
        # Exit with error code if there were errors
        if metrics.get('errors', 0) > 0:
            logger.warning(f"Completed with {metrics['errors']} errors")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Manual ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

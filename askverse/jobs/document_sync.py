import asyncio
import logging
from datetime import datetime
import argparse

from ..services.document_sync import DocumentSyncService
from ..core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_sync():
    """Run document synchronization job."""
    try:
        sync_service = DocumentSyncService()
        
        # Run document sync
        logger.info("Starting document synchronization...")
        result = await sync_service.sync_documents()
        
        if result["status"] == "success":
            logger.info(f"Sync completed successfully. Processed {result['total_documents']} documents.")
            logger.info(f"Successful: {result['successful_documents']}, Failed: {result['failed_documents']}")
        else:
            logger.error(f"Sync failed: {result['error']}")
        
        # Run cleanup if configured
        if settings.CLEANUP_OLD_DOCUMENTS:
            logger.info("Running document cleanup...")
            cleanup_result = await sync_service.cleanup_old_documents(days=settings.DOCUMENT_RETENTION_DAYS)
            
            if cleanup_result["status"] == "success":
                logger.info(f"Cleanup completed. Removed {cleanup_result['removed_documents']} documents.")
            else:
                logger.error(f"Cleanup failed: {cleanup_result['error']}")
        
    except Exception as e:
        logger.error(f"Error in sync job: {str(e)}")
        raise

def main():
    """Main entry point for the sync job."""
    parser = argparse.ArgumentParser(description="Document synchronization job")
    parser.add_argument("--cleanup", action="store_true", help="Run document cleanup")
    args = parser.parse_args()
    
    # Run the sync job
    asyncio.run(run_sync())

if __name__ == "__main__":
    main() 
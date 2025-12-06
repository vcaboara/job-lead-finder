"""Background worker process for job discovery and link finding.

This worker runs independently from the UI server, performing:
- Direct link discovery from aggregator job postings
- Automated job discovery via configured providers
- Cleanup of old hidden jobs
- Other background maintenance tasks

The worker is designed to run in a separate container, sharing the database
with the UI server but operating independently.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from app.background_scheduler import get_scheduler

# Ensure logs directory exists before configuring logging
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/worker.log"),
    ],
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


async def main():
    """Run the background worker."""
    logger.info("Starting background worker...")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting background worker...")

    # Get the scheduler singleton and start it
    scheduler = get_scheduler()

    # Configure intervals
    # - Link discovery: every 60 minutes
    # - Job cleanup: every 24 hours
    scheduler.start(
        find_links_interval_minutes=60,
        cleanup_interval_hours=24
    )
    logger.info("Background scheduler started successfully")

    # Keep the worker running until shutdown is requested
    try:
        while not shutdown_requested:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        logger.info("Shutting down background scheduler...")
        scheduler.stop()
        logger.info("Background worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Worker crashed with error: {e}", exc_info=True)
        sys.exit(1)

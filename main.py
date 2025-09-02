from scheduler import create_scheduler
from tasks import initialize_db
import logging

logger = logging.getLogger(__name__)

def main():
    logger.info("Container startup -- initializing DB and scheduler")
    initialize_db()
    scheduler = create_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received -- stopping scheduler")
        scheduler.shutdown()

if __name__ == "__main__":
    main()

# Created with AI assistance

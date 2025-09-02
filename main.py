from scheduler import create_scheduler
from tasks import initialize_db

def main():
    initialize_db()
    scheduler = create_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()

# Created with AI assistance

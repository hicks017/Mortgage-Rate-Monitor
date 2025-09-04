from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from tasks import fetch_and_store_data
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_unique_job(scheduler, job_id, func, trigger, max_instances=1):
    """
    Add a job to the scheduler, ensuring no duplicate jobs with the same ID exist.
    """
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        logger.info(f"Removing existing job -- {job_id}")
        scheduler.remove_job(job_id)
    scheduler.add_job(func, trigger, id=job_id, max_instances=max_instances)

def create_scheduler():
    """
    Create and configure the scheduler with the required jobs.
    """
    # Set timezone and schedule
    tz = pytz.timezone("America/Los_Angeles")
    hour, minute = 8,40
    sched = BlockingScheduler(timezone=tz)

    # Run daily at the scheduled time:
    daily_trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
    add_unique_job(sched, "daily_fetch_and_store", fetch_and_store_data, daily_trigger, max_instances=1)
    logger.info(
        f"Scheduled daily data fetch and store at "
        f"{hour:02d}:{minute:02d} {tz.zone}"
    )

    return sched

# Created with AI assistance

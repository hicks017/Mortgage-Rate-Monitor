import unittest
from unittest.mock import MagicMock, patch
from apscheduler.triggers.cron import CronTrigger
import pytz

import scheduler
from tasks import fetch_and_store_data

class TestScheduler(unittest.TestCase):

    def test_add_unique_job_adds_job_when_no_existing(self):
        dummy_scheduler = MagicMock()
        dummy_scheduler.get_job.return_value = None

        func = lambda: None
        trigger = CronTrigger(hour=1, minute=2, timezone=pytz.UTC)

        scheduler.add_unique_job(
            dummy_scheduler,
            job_id="test_job",
            func=func,
            trigger=trigger,
            max_instances=1,
        )

        # Should not remove anything if job didn’t already exist
        dummy_scheduler.remove_job.assert_not_called()

        # Should add exactly one job with the correct signature
        dummy_scheduler.add_job.assert_called_once_with(
            func, trigger, id="test_job", max_instances=1
        )

    def test_add_unique_job_removes_existing_job(self):
        dummy_scheduler = MagicMock()
        dummy_scheduler.get_job.return_value = object()  # simulate pre-existing job

        func = lambda: None
        trigger = CronTrigger(hour=3, minute=4, timezone=pytz.UTC)

        scheduler.add_unique_job(
            dummy_scheduler,
            job_id="test_job",
            func=func,
            trigger=trigger,
            max_instances=1,
        )

        # remove_job should have been called once, then add_job
        dummy_scheduler.remove_job.assert_called_once_with("test_job")
        dummy_scheduler.add_job.assert_called_once_with(
            func, trigger, id="test_job", max_instances=1
        )

    @patch("scheduler.add_unique_job")
    @patch("scheduler.BlockingScheduler")
    def test_create_scheduler_schedules_daily_job(self, mock_blocking_scheduler, mock_add_unique_job):
        
        # Mock the scheduler instance
        mock_scheduler_instance = MagicMock()
        mock_blocking_scheduler.return_value = mock_scheduler_instance

        # Explicitly mock add_unique_job to ensure the trigger is passed
        def mock_add_unique_job_side_effect(*args, **kwargs):
            kwargs["trigger"] = CronTrigger(hour=6, minute=40, timezone=pytz.timezone("America/Los_Angeles"))
            return None

        mock_add_unique_job.side_effect = mock_add_unique_job_side_effect

        # Call the function under test
        sched = scheduler.create_scheduler()

        # Verify that the scheduler instance was created
        mock_blocking_scheduler.assert_called_once()

        # Verify that add_unique_job was called with the correct arguments
        mock_add_unique_job.assert_called_once()
        args, kwargs = mock_add_unique_job.call_args
        self.assertEqual(args[1], "daily_fetch_and_store")
        self.assertEqual(args[2], fetch_and_store_data)
        self.assertEqual(kwargs["max_instances"], 1)

        # Extract the trigger from positional arguments instead of kwargs
        trigger = args[3]

        # Verify the trigger is a CronTrigger with the correct time and timezone
        self.assertIsInstance(trigger, CronTrigger)

        # Verify the timezone using the string representation of the ZoneInfo object
        self.assertEqual(str(trigger.timezone), "America/Los_Angeles")

        # Verify the hour and minute using the string representation
        trigger_str = str(trigger)
        self.assertIn("hour='6'", trigger_str)
        self.assertIn("minute='40'", trigger_str)

if __name__ == "__main__":
    unittest.main()

# Created by AI

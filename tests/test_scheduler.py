import pytest
from unittest.mock import MagicMock
from apscheduler.triggers.cron import CronTrigger
import pytz

import scheduler
from tasks import fetch_and_store_data


def test_add_unique_job_adds_job_when_no_existing():
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


def test_add_unique_job_removes_existing_job():
    dummy_scheduler = MagicMock()
    dummy_scheduler.get_job.return_value = object()  # simulate pre‐existing job

    func = lambda: None
    trigger = CronTrigger(hour=3, minute=4, timezone=pytz.UTC)

    scheduler.add_unique_job(
        dummy_scheduler,
        job_id="test_job",
        func=func,
        trigger=trigger,
        max_instances=1,
    )

    # Now remove_job should have been called once, then add_job
    dummy_scheduler.remove_job.assert_called_once_with("test_job")
    dummy_scheduler.add_job.assert_called_once_with(
        func, trigger, id="test_job", max_instances=1
    )


def test_create_scheduler_schedules_daily_job(monkeypatch):
    captured = []

    # Replace add_unique_job with a fake to capture its parameters
    def fake_add_unique_job(sched, job_id, func, trigger, max_instances):
        captured.append({
            "sched": sched,
            "job_id": job_id,
            "func": func,
            "trigger": trigger,
            "max_instances": max_instances
        })

    monkeypatch.setattr(scheduler, "add_unique_job", fake_add_unique_job)

    sched = scheduler.create_scheduler()

    # We should have scheduled exactly one job
    assert len(captured) == 1

    call = captured[0]
    assert call["sched"] is sched
    assert call["job_id"] == "daily_fetch_and_store"
    assert call["func"] is fetch_and_store_data

    trigger = call["trigger"]
    assert isinstance(trigger, CronTrigger)

    # Verify the CronTrigger has the right hour/minute in America/Los_Angeles
    assert hasattr(trigger, "fields")
    assert trigger.fields["hour"].allowed_values == {6}
    assert trigger.fields["minute"].allowed_values == {40}
    assert trigger.timezone.zone == "America/Los_Angeles"

    assert call["max_instances"] == 1

    # Also ensure the scheduler itself was created with the correct timezone
    assert sched.timezone.zone == "America/Los_Angeles"

# Created by AI

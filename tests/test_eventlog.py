"""Tests for cronwrap.eventlog."""
import pytest
from pathlib import Path
from cronwrap.eventlog import EventLog, EventEntry


@pytest.fixture
def log_path(tmp_path):
    return str(tmp_path / "events" / "events.jsonl")


def test_record_and_all(log_path):
    log = EventLog(log_path)
    log.record("backup", "start")
    log.record("backup", "success", exit_code=0)
    entries = log.all()
    assert len(entries) == 2
    assert entries[0].event == "start"
    assert entries[1].event == "success"
    assert entries[1].exit_code == 0


def test_empty_log_returns_empty_list(log_path):
    log = EventLog(log_path)
    assert log.all() == []


def test_for_job_filters(log_path):
    log = EventLog(log_path)
    log.record("backup", "start")
    log.record("cleanup", "start")
    log.record("backup", "success")
    result = log.for_job("backup")
    assert len(result) == 2
    assert all(e.job_name == "backup" for e in result)


def test_for_event_filters(log_path):
    log = EventLog(log_path)
    log.record("backup", "start")
    log.record("backup", "failure", exit_code=1)
    log.record("cleanup", "failure", exit_code=2)
    failures = log.for_event("failure")
    assert len(failures) == 2
    assert all(e.event == "failure" for e in failures)


def test_last_returns_most_recent(log_path):
    log = EventLog(log_path)
    log.record("backup", "start")
    log.record("backup", "retry", detail="attempt 2")
    log.record("backup", "success")
    last = log.last("backup")
    assert last is not None
    assert last.event == "success"


def test_last_returns_none_for_unknown_job(log_path):
    log = EventLog(log_path)
    assert log.last("nonexistent") is None


def test_round_trip_dict():
    from datetime import timezone, datetime
    entry = EventEntry(
        job_name="test",
        event="skip",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        detail="skipped due to skiplist",
        exit_code=None,
    )
    restored = EventEntry.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.event == entry.event
    assert restored.detail == entry.detail
    assert restored.exit_code is None


def test_detail_stored(log_path):
    log = EventLog(log_path)
    log.record("myjob", "failure", detail="timeout exceeded", exit_code=124)
    entry = log.last("myjob")
    assert entry.detail == "timeout exceeded"
    assert entry.exit_code == 124

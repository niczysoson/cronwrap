"""Tests for cronwrap.cleanup retention/purge logic."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from cronwrap.cleanup import RetentionPolicy, purge_history, purge_audit
from cronwrap.history import HistoryEntry
from cronwrap.audit import AuditEvent


def _entry(name="job", days_ago=0, success=True):
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    e = MagicMock(spec=HistoryEntry)
    e.job_name = name
    e.started_at = ts
    e.succeeded = success
    return e


def _event(name="job", days_ago=0):
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    ev = MagicMock(spec=AuditEvent)
    ev.job_name = name
    ev.timestamp = ts
    return ev


def _mock_history(entries):
    h = MagicMock()
    h.get_all.return_value = list(entries)
    h._entries = list(entries)
    return h


def _mock_audit(events):
    a = MagicMock()
    a.read.side_effect = lambda job_name=None: (
        [e for e in events if e.job_name == job_name] if job_name else list(events)
    )
    a._events = list(events)
    return a


def test_policy_defaults():
    p = RetentionPolicy()
    assert p.max_age_days == 30
    assert p.max_entries == 500
    assert p.job_name is None


def test_policy_invalid_age():
    with pytest.raises(ValueError):
        RetentionPolicy(max_age_days=0)


def test_policy_invalid_entries():
    with pytest.raises(ValueError):
        RetentionPolicy(max_entries=0)


def test_policy_from_dict():
    p = RetentionPolicy.from_dict({"max_age_days": 7, "max_entries": 100, "job_name": "backup"})
    assert p.max_age_days == 7
    assert p.job_name == "backup"


def test_purge_history_removes_old_entries():
    entries = [_entry(days_ago=0), _entry(days_ago=10), _entry(days_ago=40)]
    h = _mock_history(entries)
    removed = purge_history(h, RetentionPolicy(max_age_days=30))
    assert removed == 1


def test_purge_history_respects_max_entries():
    entries = [_entry(days_ago=i) for i in range(10)]
    h = _mock_history(entries)
    removed = purge_history(h, RetentionPolicy(max_age_days=30, max_entries=5))
    assert removed == 5


def test_purge_history_scoped_to_job():
    entries = [_entry("job_a", days_ago=40), _entry("job_b", days_ago=40)]
    h = _mock_history(entries)
    removed = purge_history(h, RetentionPolicy(max_age_days=30, job_name="job_a"))
    assert removed == 1


def test_purge_audit_removes_old_events():
    events = [_event(days_ago=0), _event(days_ago=5), _event(days_ago=60)]
    a = _mock_audit(events)
    removed = purge_audit(a, RetentionPolicy(max_age_days=30))
    assert removed == 1

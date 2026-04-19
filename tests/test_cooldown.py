"""Tests for cronwrap.cooldown."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwrap.cooldown import (
    CooldownConfig,
    cooldown_from_dict,
    last_failure_time,
    is_cooling_down,
    seconds_remaining,
)
from cronwrap.history import HistoryEntry


def _entry(succeeded: bool, minutes_ago: float = 1.0) -> HistoryEntry:
    now = datetime.now(timezone.utc)
    finished = now - timedelta(minutes=minutes_ago)
    e = MagicMock(spec=HistoryEntry)
    e.succeeded = succeeded
    e.finished_at = finished
    return e


def _mock_history(entries):
    h = MagicMock()
    h.get.return_value = entries
    return h


def test_config_valid():
    c = CooldownConfig(seconds=60, job_name="job")
    assert c.seconds == 60


def test_config_invalid():
    with pytest.raises(ValueError):
        CooldownConfig(seconds=-1)


def test_cooldown_from_dict():
    c = cooldown_from_dict({"seconds": 120, "job_name": "myjob"})
    assert c.seconds == 120
    assert c.job_name == "myjob"


def test_cooldown_from_dict_defaults():
    c = cooldown_from_dict({})
    assert c.seconds == 300


def test_last_failure_time_no_entries():
    h = _mock_history([])
    assert last_failure_time("job", h) is None


def test_last_failure_time_only_successes():
    h = _mock_history([_entry(True, 2), _entry(True, 1)])
    assert last_failure_time("job", h) is None


def test_last_failure_time_returns_most_recent():
    old = _entry(False, 10)
    recent = _entry(False, 2)
    h = _mock_history([old, recent])
    result = last_failure_time("job", h)
    assert result == recent.finished_at


def test_is_cooling_down_no_failures():
    h = _mock_history([])
    cfg = CooldownConfig(seconds=300, job_name="job")
    assert not is_cooling_down(cfg, h)


def test_is_cooling_down_within_window():
    h = _mock_history([_entry(False, minutes_ago=0.5)])
    cfg = CooldownConfig(seconds=300, job_name="job")
    assert is_cooling_down(cfg, h)


def test_is_cooling_down_outside_window():
    h = _mock_history([_entry(False, minutes_ago=10)])
    cfg = CooldownConfig(seconds=60, job_name="job")
    assert not is_cooling_down(cfg, h)


def test_is_cooling_down_zero_seconds_always_false():
    h = _mock_history([_entry(False, minutes_ago=0.1)])
    cfg = CooldownConfig(seconds=0, job_name="job")
    assert not is_cooling_down(cfg, h)


def test_seconds_remaining_positive():
    h = _mock_history([_entry(False, minutes_ago=0.5)])
    cfg = CooldownConfig(seconds=300, job_name="job")
    rem = seconds_remaining(cfg, h)
    assert 0 < rem < 300


def test_seconds_remaining_not_cooling():
    h = _mock_history([])
    cfg = CooldownConfig(seconds=300, job_name="job")
    assert seconds_remaining(cfg, h) == 0.0

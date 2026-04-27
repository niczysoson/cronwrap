"""Tests for cronwrap.cooldown_window."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwrap.cooldown_window import (
    CooldownWindowConfig,
    cooldown_window_from_dict,
    last_success_time,
    is_in_cooldown_window,
    seconds_remaining,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


def _entry(succeeded: bool, finished_at: datetime):
    e = MagicMock()
    e.succeeded = succeeded
    e.finished_at = finished_at
    return e


def _mock_history(job_name: str, entries):
    h = MagicMock()
    h.for_job.side_effect = lambda name: entries if name == job_name else []
    return h


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = CooldownWindowConfig(min_interval_seconds=300, job_name="backup")
    assert cfg.min_interval_seconds == 300
    assert cfg.enabled is True


def test_config_invalid_interval():
    with pytest.raises(ValueError, match="min_interval_seconds"):
        CooldownWindowConfig(min_interval_seconds=0, job_name="backup")


def test_config_invalid_empty_job_name():
    with pytest.raises(ValueError, match="job_name"):
        CooldownWindowConfig(min_interval_seconds=60, job_name="   ")


def test_cooldown_window_from_dict():
    cfg = cooldown_window_from_dict({"min_interval_seconds": 120, "job_name": "sync"})
    assert cfg.min_interval_seconds == 120
    assert cfg.job_name == "sync"
    assert cfg.enabled is True


def test_cooldown_window_from_dict_disabled():
    cfg = cooldown_window_from_dict(
        {"min_interval_seconds": 60, "job_name": "sync", "enabled": False}
    )
    assert cfg.enabled is False


# ---------------------------------------------------------------------------
# last_success_time
# ---------------------------------------------------------------------------

def test_last_success_time_no_entries():
    cfg = CooldownWindowConfig(min_interval_seconds=60, job_name="job")
    h = _mock_history("job", [])
    assert last_success_time(cfg, h) is None


def test_last_success_time_only_failures():
    cfg = CooldownWindowConfig(min_interval_seconds=60, job_name="job")
    entries = [_entry(False, _utc(-100))]
    h = _mock_history("job", entries)
    assert last_success_time(cfg, h) is None


def test_last_success_time_returns_most_recent():
    cfg = CooldownWindowConfig(min_interval_seconds=60, job_name="job")
    entries = [
        _entry(True, _utc(-500)),
        _entry(True, _utc(-200)),
        _entry(False, _utc(-50)),
    ]
    h = _mock_history("job", entries)
    assert last_success_time(cfg, h) == _utc(-200)


# ---------------------------------------------------------------------------
# is_in_cooldown_window
# ---------------------------------------------------------------------------

def test_not_in_cooldown_when_disabled():
    cfg = CooldownWindowConfig(min_interval_seconds=3600, job_name="job", enabled=False)
    entries = [_entry(True, _utc(-10))]
    h = _mock_history("job", entries)
    assert is_in_cooldown_window(cfg, h, now=_utc()) is False


def test_not_in_cooldown_when_no_history():
    cfg = CooldownWindowConfig(min_interval_seconds=3600, job_name="job")
    h = _mock_history("job", [])
    assert is_in_cooldown_window(cfg, h, now=_utc()) is False


def test_in_cooldown_when_recent_success():
    cfg = CooldownWindowConfig(min_interval_seconds=3600, job_name="job")
    entries = [_entry(True, _utc(-100))]
    h = _mock_history("job", entries)
    assert is_in_cooldown_window(cfg, h, now=_utc()) is True


def test_not_in_cooldown_when_success_is_old():
    cfg = CooldownWindowConfig(min_interval_seconds=3600, job_name="job")
    entries = [_entry(True, _utc(-7200))]
    h = _mock_history("job", entries)
    assert is_in_cooldown_window(cfg, h, now=_utc()) is False


# ---------------------------------------------------------------------------
# seconds_remaining
# ---------------------------------------------------------------------------

def test_seconds_remaining_when_cooling():
    cfg = CooldownWindowConfig(min_interval_seconds=600, job_name="job")
    entries = [_entry(True, _utc(-100))]
    h = _mock_history("job", entries)
    rem = seconds_remaining(cfg, h, now=_utc())
    assert abs(rem - 500.0) < 1.0


def test_seconds_remaining_zero_when_expired():
    cfg = CooldownWindowConfig(min_interval_seconds=60, job_name="job")
    entries = [_entry(True, _utc(-120))]
    h = _mock_history("job", entries)
    assert seconds_remaining(cfg, h, now=_utc()) == 0.0


def test_seconds_remaining_zero_when_disabled():
    cfg = CooldownWindowConfig(min_interval_seconds=600, job_name="job", enabled=False)
    entries = [_entry(True, _utc(-10))]
    h = _mock_history("job", entries)
    assert seconds_remaining(cfg, h, now=_utc()) == 0.0

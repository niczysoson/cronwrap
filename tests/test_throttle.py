"""Tests for cronwrap.throttle."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cronwrap.throttle import (
    ThrottleConfig,
    is_throttled,
    last_success_time,
    throttle_from_dict,
)
from cronwrap.history import HistoryEntry


def _make_entry(job_name: str, succeeded: bool, started_at: float) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.job_name = job_name
    e.succeeded = succeeded
    e.started_at = started_at
    return e


def _mock_history(entries):
    h = MagicMock()
    h.get.return_value = entries
    return h


def test_throttle_config_valid():
    cfg = ThrottleConfig(min_interval_seconds=300)
    assert cfg.min_interval_seconds == 300


def test_throttle_config_invalid():
    with pytest.raises(ValueError):
        ThrottleConfig(min_interval_seconds=-1)


def test_last_success_time_no_entries():
    h = _mock_history([])
    assert last_success_time("job", h) is None


def test_last_success_time_only_failures():
    now = time.time()
    h = _mock_history([_make_entry("job", False, now)])
    assert last_success_time("job", h) is None


def test_last_success_time_returns_max():
    now = time.time()
    entries = [
        _make_entry("job", True, now - 100),
        _make_entry("job", True, now - 10),
        _make_entry("job", False, now - 1),
    ]
    h = _mock_history(entries)
    result = last_success_time("job", h)
    assert abs(result - (now - 10)) < 0.01


def test_is_throttled_no_history():
    h = _mock_history([])
    cfg = ThrottleConfig(min_interval_seconds=300)
    assert is_throttled("job", cfg, h) is False


def test_is_throttled_recent_success():
    now = time.time()
    h = _mock_history([_make_entry("job", True, now - 60)])
    cfg = ThrottleConfig(min_interval_seconds=300)
    assert is_throttled("job", cfg, h) is True


def test_is_throttled_old_success():
    now = time.time()
    h = _mock_history([_make_entry("job", True, now - 400)])
    cfg = ThrottleConfig(min_interval_seconds=300)
    assert is_throttled("job", cfg, h) is False


def test_throttle_from_dict():
    cfg = throttle_from_dict({"min_interval_seconds": "120", "state_dir": "/tmp"})
    assert cfg.min_interval_seconds == 120
    assert cfg.state_dir.as_posix() == "/tmp"


def test_throttle_from_dict_empty():
    assert throttle_from_dict({}) is None
    assert throttle_from_dict(None) is None

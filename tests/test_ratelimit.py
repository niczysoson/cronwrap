"""Tests for cronwrap.ratelimit."""
import time
from unittest.mock import MagicMock

import pytest

from cronwrap.ratelimit import (
    RateLimitConfig,
    rate_limit_from_dict,
    count_recent_runs,
    is_rate_limited,
    rate_limit_status,
)
from cronwrap.history import HistoryEntry


def _entry(succeeded: bool, offset: float = 0.0) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.succeeded = succeeded
    e.started_at = time.time() - offset
    return e


def _store(entries):
    store = MagicMock()
    store.get.return_value = entries
    return store


def test_config_valid():
    cfg = RateLimitConfig(max_runs=5, window_seconds=3600)
    assert cfg.max_runs == 5


def test_config_invalid_runs():
    with pytest.raises(ValueError):
        RateLimitConfig(max_runs=0, window_seconds=60)


def test_config_invalid_window():
    with pytest.raises(ValueError):
        RateLimitConfig(max_runs=1, window_seconds=0)


def test_rate_limit_from_dict():
    cfg = rate_limit_from_dict({"max_runs": "3", "window_seconds": "600"})
    assert cfg.max_runs == 3
    assert cfg.window_seconds == 600


def test_rate_limit_from_dict_none():
    assert rate_limit_from_dict({}) is None


def test_count_recent_runs_all_recent():
    entries = [_entry(True), _entry(True), _entry(False)]
    assert count_recent_runs(entries, 3600) == 2


def test_count_recent_runs_some_old():
    entries = [_entry(True, offset=10), _entry(True, offset=7200)]
    assert count_recent_runs(entries, 3600) == 1


def test_is_rate_limited_true():
    cfg = RateLimitConfig(max_runs=2, window_seconds=3600)
    entries = [_entry(True), _entry(True)]
    assert is_rate_limited("myjob", cfg, _store(entries)) is True


def test_is_rate_limited_false():
    cfg = RateLimitConfig(max_runs=3, window_seconds=3600)
    entries = [_entry(True)]
    assert is_rate_limited("myjob", cfg, _store(entries)) is False


def test_rate_limit_status_fields():
    cfg = RateLimitConfig(max_runs=2, window_seconds=60)
    entries = [_entry(True)]
    status = rate_limit_status("job", cfg, _store(entries))
    assert status["recent_runs"] == 1
    assert status["limited"] is False
    assert status["job"] == "job"

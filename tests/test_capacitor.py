"""Tests for cronwrap.capacitor."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cronwrap.capacitor import (
    CapacitorConfig,
    CapacitorResult,
    capacitor_from_dict,
    check_capacity,
    count_starts_in_window,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _utc(**kw) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kw)


def _make_entry(started_at: datetime):
    e = MagicMock()
    e.started_at = started_at
    return e


def _mock_history(entries):
    store = MagicMock()
    store.for_job.return_value = entries
    return store


# ---------------------------------------------------------------------------
# CapacitorConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = CapacitorConfig(max_starts=3, window_seconds=60)
    assert cfg.max_starts == 3
    assert cfg.window_seconds == 60
    assert cfg.enabled is True


def test_config_invalid_max_starts():
    with pytest.raises(ValueError, match="max_starts"):
        CapacitorConfig(max_starts=0)


def test_config_invalid_window():
    with pytest.raises(ValueError, match="window_seconds"):
        CapacitorConfig(window_seconds=0)


def test_config_invalid_enabled_type():
    with pytest.raises(TypeError, match="enabled"):
        CapacitorConfig(enabled="yes")  # type: ignore


def test_capacitor_from_dict():
    cfg = capacitor_from_dict({"max_starts": 10, "window_seconds": 120, "enabled": False})
    assert cfg.max_starts == 10
    assert cfg.window_seconds == 120
    assert cfg.enabled is False


def test_capacitor_from_dict_defaults():
    cfg = capacitor_from_dict({})
    assert cfg.max_starts == 5
    assert cfg.window_seconds == 3600
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# count_starts_in_window
# ---------------------------------------------------------------------------

def test_count_starts_none_recent():
    entries = [_make_entry(_utc(seconds=7200))]  # outside 1-hour window
    store = _mock_history(entries)
    assert count_starts_in_window("job", store, 3600) == 0


def test_count_starts_some_recent():
    entries = [
        _make_entry(_utc(seconds=100)),
        _make_entry(_utc(seconds=200)),
        _make_entry(_utc(seconds=7200)),  # old
    ]
    store = _mock_history(entries)
    assert count_starts_in_window("job", store, 3600) == 2


# ---------------------------------------------------------------------------
# check_capacity
# ---------------------------------------------------------------------------

def test_check_capacity_allowed():
    store = _mock_history([_make_entry(_utc(seconds=30))])
    cfg = CapacitorConfig(max_starts=3, window_seconds=3600)
    result = check_capacity("job", cfg, store)
    assert result.allowed is True
    assert result.starts_in_window == 1


def test_check_capacity_blocked():
    entries = [_make_entry(_utc(seconds=i * 10)) for i in range(5)]
    store = _mock_history(entries)
    cfg = CapacitorConfig(max_starts=5, window_seconds=3600)
    result = check_capacity("job", cfg, store)
    assert result.allowed is False
    assert result.starts_in_window == 5


def test_check_capacity_disabled_always_allowed():
    entries = [_make_entry(_utc(seconds=i * 10)) for i in range(100)]
    store = _mock_history(entries)
    cfg = CapacitorConfig(max_starts=1, window_seconds=3600, enabled=False)
    result = check_capacity("job", cfg, store)
    assert result.allowed is True
    assert result.starts_in_window == 0


def test_result_summary_allowed():
    r = CapacitorResult(allowed=True, starts_in_window=2, max_starts=5, window_seconds=60)
    assert "allowed" in r.summary()
    assert "2/5" in r.summary()


def test_result_summary_blocked():
    r = CapacitorResult(allowed=False, starts_in_window=5, max_starts=5, window_seconds=60)
    assert "blocked" in r.summary()

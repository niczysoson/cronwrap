"""Tests for cronwrap.pincount."""
from __future__ import annotations

import datetime
import pytest
from unittest.mock import MagicMock

from cronwrap.pincount import (
    PinCountConfig,
    PinCountResult,
    pincount_from_dict,
    count_pins_in_window,
    is_pin_count_exceeded,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(succeeded: bool, seconds_ago: float = 10):
    e = MagicMock()
    e.succeeded = succeeded
    e.finished_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds_ago)
    return e


def _store(entries):
    s = MagicMock()
    s.for_job.return_value = entries
    return s


# ---------------------------------------------------------------------------
# PinCountConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = PinCountConfig(enabled=True, job_name="backup", max_pins=5, window_seconds=7200)
    assert cfg.max_pins == 5
    assert cfg.window_seconds == 7200


def test_config_invalid_max_pins():
    with pytest.raises(ValueError, match="max_pins"):
        PinCountConfig(max_pins=0)


def test_config_invalid_window():
    with pytest.raises(ValueError, match="window_seconds"):
        PinCountConfig(window_seconds=0)


def test_config_invalid_enabled_type():
    with pytest.raises(TypeError):
        PinCountConfig(enabled="yes")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# pincount_from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = pincount_from_dict({})
    assert cfg.enabled is True
    assert cfg.max_pins == 3
    assert cfg.window_seconds == 3600


def test_from_dict_custom():
    cfg = pincount_from_dict({"job_name": "sync", "max_pins": 2, "window_seconds": 600})
    assert cfg.job_name == "sync"
    assert cfg.max_pins == 2


# ---------------------------------------------------------------------------
# count_pins_in_window
# ---------------------------------------------------------------------------

def test_count_pins_no_failures():
    store = _store([_entry(True), _entry(True)])
    assert count_pins_in_window("job", 3600, store) == 0


def test_count_pins_counts_failures():
    store = _store([_entry(False), _entry(False), _entry(True)])
    assert count_pins_in_window("job", 3600, store) == 2


def test_count_pins_ignores_old_failures():
    old = _entry(False, seconds_ago=7200)
    recent = _entry(False, seconds_ago=60)
    store = _store([old, recent])
    assert count_pins_in_window("job", 3600, store) == 1


# ---------------------------------------------------------------------------
# is_pin_count_exceeded
# ---------------------------------------------------------------------------

def test_not_exceeded():
    cfg = PinCountConfig(job_name="j", max_pins=3)
    store = _store([_entry(False), _entry(True)])
    result = is_pin_count_exceeded(cfg, store)
    assert not result.exceeded
    assert result.pinned_count == 1


def test_exceeded():
    cfg = PinCountConfig(job_name="j", max_pins=2)
    store = _store([_entry(False), _entry(False), _entry(False)])
    result = is_pin_count_exceeded(cfg, store)
    assert result.exceeded
    assert "blocked" in result.summary()


def test_disabled_never_exceeded():
    cfg = PinCountConfig(enabled=False, job_name="j", max_pins=1)
    store = _store([_entry(False)] * 10)
    result = is_pin_count_exceeded(cfg, store)
    assert not result.exceeded
    assert "disabled" in result.summary()

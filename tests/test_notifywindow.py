"""Tests for cronwrap.notifywindow."""
from __future__ import annotations

import pytest
from datetime import datetime

from cronwrap.notifywindow import (
    NotifyWindowConfig,
    NotifyWindowResult,
    is_notify_allowed,
    notify_window_from_dict,
    _parse_time,
    _parse_window,
)


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_default_config_is_valid():
    cfg = NotifyWindowConfig()
    assert cfg.enabled is True
    assert cfg.windows == []


def test_config_invalid_enabled_type():
    with pytest.raises(ValueError, match="enabled"):
        NotifyWindowConfig(enabled="yes")  # type: ignore


def test_config_invalid_windows_type():
    with pytest.raises(ValueError, match="windows"):
        NotifyWindowConfig(windows="08:00-18:00")  # type: ignore


def test_config_invalid_window_format():
    with pytest.raises(ValueError):
        NotifyWindowConfig(windows=["0800-1800"])


def test_config_invalid_window_start_after_end():
    with pytest.raises(ValueError, match="start must be before end"):
        NotifyWindowConfig(windows=["18:00-08:00"])


def test_config_valid_window():
    cfg = NotifyWindowConfig(windows=["09:00-17:00"])
    assert len(cfg.windows) == 1


# ---------------------------------------------------------------------------
# _parse_time / _parse_window
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    t = _parse_time("08:30")
    assert t.hour == 8 and t.minute == 30


def test_parse_time_invalid_format():
    with pytest.raises(ValueError):
        _parse_time("8am")


def test_parse_time_out_of_range():
    with pytest.raises(ValueError):
        _parse_time("25:00")


# ---------------------------------------------------------------------------
# is_notify_allowed
# ---------------------------------------------------------------------------

def _dt(h: int, m: int) -> datetime:
    return datetime(2024, 6, 15, h, m, 0)


def test_disabled_always_allowed():
    cfg = NotifyWindowConfig(enabled=False, windows=["09:00-17:00"])
    result = is_notify_allowed(cfg, now=_dt(3, 0))
    assert result.allowed is True


def test_no_windows_always_allowed():
    cfg = NotifyWindowConfig(windows=[])
    result = is_notify_allowed(cfg, now=_dt(3, 0))
    assert result.allowed is True


def test_within_single_window():
    cfg = NotifyWindowConfig(windows=["08:00-18:00"])
    result = is_notify_allowed(cfg, now=_dt(12, 0))
    assert result.allowed is True
    assert "within window" in result.reason


def test_outside_single_window():
    cfg = NotifyWindowConfig(windows=["08:00-18:00"])
    result = is_notify_allowed(cfg, now=_dt(2, 0))
    assert result.allowed is False
    assert "outside" in result.reason


def test_within_second_of_two_windows():
    cfg = NotifyWindowConfig(windows=["06:00-09:00", "20:00-23:00"])
    result = is_notify_allowed(cfg, now=_dt(21, 30))
    assert result.allowed is True


def test_boundary_start_is_included():
    cfg = NotifyWindowConfig(windows=["08:00-18:00"])
    result = is_notify_allowed(cfg, now=_dt(8, 0))
    assert result.allowed is True


def test_boundary_end_is_included():
    cfg = NotifyWindowConfig(windows=["08:00-18:00"])
    result = is_notify_allowed(cfg, now=_dt(18, 0))
    assert result.allowed is True


# ---------------------------------------------------------------------------
# notify_window_from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = notify_window_from_dict({})
    assert cfg.enabled is True
    assert cfg.windows == []
    assert cfg.timezone == "UTC"


def test_from_dict_full():
    cfg = notify_window_from_dict(
        {"enabled": False, "windows": ["09:00-17:00"], "timezone": "Europe/London"}
    )
    assert cfg.enabled is False
    assert cfg.windows == ["09:00-17:00"]
    assert cfg.timezone == "Europe/London"


# ---------------------------------------------------------------------------
# NotifyWindowResult.summary
# ---------------------------------------------------------------------------

def test_result_summary_allowed():
    r = NotifyWindowResult(allowed=True, reason="within window 09:00-17:00")
    assert "allowed" in r.summary()


def test_result_summary_suppressed():
    r = NotifyWindowResult(allowed=False, reason="outside all windows at 03:00")
    assert "suppressed" in r.summary()

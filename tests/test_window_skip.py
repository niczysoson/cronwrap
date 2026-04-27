"""Tests for cronwrap.window_skip."""
import datetime
import pytest

from cronwrap.window_skip import (
    WindowSkipConfig,
    window_skip_from_dict,
    should_skip,
    skip_reason,
)

_TODAY = datetime.date(2024, 6, 15)
_BEFORE = datetime.date(2024, 6, 1)
_AFTER = datetime.date(2024, 6, 30)


def test_default_config_always_in_window():
    cfg = WindowSkipConfig()
    assert cfg.is_in_window(_TODAY) is True


def test_disabled_config_always_in_window():
    cfg = WindowSkipConfig(enabled=False, start_date=_AFTER, end_date=_AFTER)
    assert cfg.is_in_window(_TODAY) is True


def test_in_window_between_dates():
    cfg = WindowSkipConfig(start_date=_BEFORE, end_date=_AFTER)
    assert cfg.is_in_window(_TODAY) is True


def test_before_start_date_not_in_window():
    cfg = WindowSkipConfig(start_date=_AFTER)
    assert cfg.is_in_window(_TODAY) is False


def test_after_end_date_not_in_window():
    cfg = WindowSkipConfig(end_date=_BEFORE)
    assert cfg.is_in_window(_TODAY) is False


def test_invalid_date_range_raises():
    with pytest.raises(ValueError, match="start_date"):
        WindowSkipConfig(start_date=_AFTER, end_date=_BEFORE)


def test_should_skip_outside_window():
    cfg = WindowSkipConfig(start_date=_AFTER)
    assert should_skip(cfg, _TODAY) is True


def test_should_not_skip_inside_window():
    cfg = WindowSkipConfig(start_date=_BEFORE, end_date=_AFTER)
    assert should_skip(cfg, _TODAY) is False


def test_should_not_skip_when_disabled():
    cfg = WindowSkipConfig(enabled=False, end_date=_BEFORE)
    assert should_skip(cfg, _TODAY) is False


def test_skip_reason_before_start():
    cfg = WindowSkipConfig(start_date=_AFTER)
    reason = skip_reason(cfg, _TODAY)
    assert "before start_date" in reason


def test_skip_reason_after_end():
    cfg = WindowSkipConfig(end_date=_BEFORE)
    reason = skip_reason(cfg, _TODAY)
    assert "after end_date" in reason


def test_skip_reason_within_window():
    cfg = WindowSkipConfig(start_date=_BEFORE, end_date=_AFTER)
    assert skip_reason(cfg, _TODAY) == "within window"


def test_window_skip_from_dict_full():
    cfg = window_skip_from_dict({
        "enabled": True,
        "start_date": "2024-06-01",
        "end_date": "2024-06-30",
        "soft": True,
    })
    assert cfg.start_date == _BEFORE
    assert cfg.end_date == _AFTER
    assert cfg.soft is True


def test_window_skip_from_dict_defaults():
    cfg = window_skip_from_dict({})
    assert cfg.enabled is True
    assert cfg.start_date is None
    assert cfg.end_date is None
    assert cfg.soft is False


def test_to_dict_round_trip():
    cfg = WindowSkipConfig(start_date=_BEFORE, end_date=_AFTER, soft=True)
    d = cfg.to_dict()
    assert d["start_date"] == "2024-06-01"
    assert d["end_date"] == "2024-06-30"
    assert d["soft"] is True


def test_to_dict_none_dates():
    cfg = WindowSkipConfig()
    d = cfg.to_dict()
    assert d["start_date"] is None
    assert d["end_date"] is None

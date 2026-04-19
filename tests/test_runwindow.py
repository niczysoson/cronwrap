"""Tests for cronwrap.runwindow."""
import pytest
from datetime import datetime
from cronwrap.runwindow import RunWindowConfig, runwindow_from_dict, _parse_time


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 15, hour, minute, 0)


def test_parse_time_valid():
    t = _parse_time("09:30")
    assert t.hour == 9 and t.minute == 30


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        _parse_time("25:00")
    with pytest.raises(ValueError):
        _parse_time("not-a-time")


def test_invalid_window_start_after_end():
    with pytest.raises(ValueError, match="must be before"):
        RunWindowConfig(windows=[("18:00", "08:00")])


def test_empty_windows_raises():
    with pytest.raises(ValueError, match="At least one"):
        RunWindowConfig(windows=[])


def test_is_allowed_within_window():
    cfg = RunWindowConfig(windows=[("08:00", "18:00")])
    assert cfg.is_allowed(_dt(12)) is True
    assert cfg.is_allowed(_dt(8)) is True
    assert cfg.is_allowed(_dt(18)) is True


def test_is_allowed_outside_window():
    cfg = RunWindowConfig(windows=[("08:00", "18:00")])
    assert cfg.is_allowed(_dt(7, 59)) is False
    assert cfg.is_allowed(_dt(18, 1)) is False


def test_is_allowed_disabled_always_true():
    cfg = RunWindowConfig(windows=[("08:00", "10:00")], enabled=False)
    assert cfg.is_allowed(_dt(3)) is True


def test_multiple_windows():
    cfg = RunWindowConfig(windows=[("06:00", "09:00"), ("17:00", "20:00")])
    assert cfg.is_allowed(_dt(7)) is True
    assert cfg.is_allowed(_dt(18)) is True
    assert cfg.is_allowed(_dt(12)) is False


def test_next_window_start_found():
    cfg = RunWindowConfig(windows=[("08:00", "12:00"), ("14:00", "18:00")])
    nxt = cfg.next_window_start(_dt(13))
    assert nxt is not None and nxt.hour == 14


def test_next_window_start_none_when_past_all():
    cfg = RunWindowConfig(windows=[("08:00", "12:00")])
    nxt = cfg.next_window_start(_dt(20))
    assert nxt is None


def test_to_dict():
    cfg = RunWindowConfig(windows=[("09:00", "17:00")], timezone="Europe/London")
    d = cfg.to_dict()
    assert d["windows"] == [{"start": "09:00", "end": "17:00"}]
    assert d["timezone"] == "Europe/London"
    assert d["enabled"] is True


def test_runwindow_from_dict():
    data = {
        "windows": [{"start": "07:00", "end": "19:00"}],
        "enabled": True,
        "timezone": "UTC",
    }
    cfg = runwindow_from_dict(data)
    assert cfg.is_allowed(_dt(10)) is True
    assert cfg.is_allowed(_dt(20)) is False

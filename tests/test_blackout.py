"""Tests for cronwrap.blackout and cronwrap.cli_blackout."""
from __future__ import annotations

import pytest
from datetime import datetime, time

from cronwrap.blackout import BlackoutConfig, blackout_from_dict
from cronwrap.cli_blackout import render_blackout_status, check_and_exit_if_blacked_out


# ---------------------------------------------------------------------------
# BlackoutConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = BlackoutConfig(windows=["22:00-06:00", "12:00-13:00"])
    assert cfg.enabled is True
    assert len(cfg.windows) == 2


def test_config_invalid_format():
    with pytest.raises(ValueError, match="Invalid blackout window"):
        BlackoutConfig(windows=["bad-window"])


def test_config_invalid_windows_type():
    with pytest.raises(ValueError, match="windows must be a list"):
        BlackoutConfig(windows="22:00-06:00")  # type: ignore[arg-type]


def test_disabled_never_blacked_out():
    cfg = BlackoutConfig(windows=["00:00-23:59"], enabled=False)
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 12, 0)) is False


def test_no_windows_not_blacked_out():
    cfg = BlackoutConfig(windows=[])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 12, 0)) is False


def test_within_simple_window():
    cfg = BlackoutConfig(windows=["12:00-13:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 12, 30)) is True


def test_outside_simple_window():
    cfg = BlackoutConfig(windows=["12:00-13:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 14, 0)) is False


def test_window_at_exact_start():
    cfg = BlackoutConfig(windows=["12:00-13:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 12, 0)) is True


def test_window_at_exact_end_is_clear():
    cfg = BlackoutConfig(windows=["12:00-13:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 13, 0)) is False


def test_midnight_wrap_inside():
    cfg = BlackoutConfig(windows=["22:00-06:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 23, 0)) is True
    assert cfg.is_blacked_out(datetime(2024, 1, 2, 3, 0)) is True


def test_midnight_wrap_outside():
    cfg = BlackoutConfig(windows=["22:00-06:00"])
    assert cfg.is_blacked_out(datetime(2024, 1, 1, 10, 0)) is False


def test_blackout_from_dict():
    cfg = blackout_from_dict({"windows": ["01:00-02:00"], "enabled": False})
    assert cfg.enabled is False
    assert cfg.windows == ["01:00-02:00"]


def test_blackout_from_dict_defaults():
    cfg = blackout_from_dict({})
    assert cfg.windows == []
    assert cfg.enabled is True


def test_to_dict_round_trip():
    cfg = BlackoutConfig(windows=["08:00-09:00"], enabled=True)
    assert blackout_from_dict(cfg.to_dict()).windows == ["08:00-09:00"]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_disabled():
    cfg = BlackoutConfig(windows=["12:00-13:00"], enabled=False)
    assert "disabled" in render_blackout_status(cfg)


def test_render_no_windows():
    cfg = BlackoutConfig(windows=[])
    assert "no windows" in render_blackout_status(cfg)


def test_render_blocked():
    cfg = BlackoutConfig(windows=["12:00-14:00"])
    out = render_blackout_status(cfg, now=datetime(2024, 1, 1, 12, 30))
    assert "BLOCKED" in out
    assert "12:00-14:00" in out


def test_render_clear():
    cfg = BlackoutConfig(windows=["12:00-14:00"])
    out = render_blackout_status(cfg, now=datetime(2024, 1, 1, 15, 0))
    assert "clear" in out


def test_check_and_exit_if_blacked_out(monkeypatch):
    cfg = BlackoutConfig(windows=["12:00-14:00"])
    exited = {}
    monkeypatch.setattr("sys.exit", lambda code: exited.update({"code": code}))
    check_and_exit_if_blacked_out(cfg, now=datetime(2024, 1, 1, 12, 30), exit_code=2)
    assert exited["code"] == 2


def test_check_no_exit_when_clear(monkeypatch):
    cfg = BlackoutConfig(windows=["12:00-14:00"])
    monkeypatch.setattr("sys.exit", lambda code: (_ for _ in ()).throw(AssertionError("should not exit")))
    check_and_exit_if_blacked_out(cfg, now=datetime(2024, 1, 1, 15, 0))

"""Tests for cronwrap.cli_notifywindow."""
from __future__ import annotations

import sys
from datetime import datetime

import pytest

from cronwrap.notifywindow import NotifyWindowConfig
from cronwrap.cli_notifywindow import (
    render_notify_window_config,
    render_notify_window_result,
    check_and_exit_if_suppressed,
)
from cronwrap.notifywindow import NotifyWindowResult


def _dt(h: int, m: int) -> datetime:
    return datetime(2024, 6, 15, h, m, 0)


# ---------------------------------------------------------------------------
# render_notify_window_config
# ---------------------------------------------------------------------------

def test_render_config_no_windows():
    cfg = NotifyWindowConfig()
    out = render_notify_window_config(cfg)
    assert "enabled" in out
    assert "always allowed" in out


def test_render_config_with_windows():
    cfg = NotifyWindowConfig(windows=["09:00-17:00", "20:00-22:00"])
    out = render_notify_window_config(cfg)
    assert "09:00-17:00" in out
    assert "20:00-22:00" in out


def test_render_config_disabled():
    cfg = NotifyWindowConfig(enabled=False)
    out = render_notify_window_config(cfg)
    assert "False" in out


# ---------------------------------------------------------------------------
# render_notify_window_result
# ---------------------------------------------------------------------------

def test_render_result_allowed():
    r = NotifyWindowResult(allowed=True, reason="within window 09:00-17:00")
    out = render_notify_window_result(r)
    assert "\u2705" in out
    assert "allowed" in out


def test_render_result_suppressed():
    r = NotifyWindowResult(allowed=False, reason="outside all windows at 03:00")
    out = render_notify_window_result(r)
    assert "\u274c" in out
    assert "suppressed" in out


# ---------------------------------------------------------------------------
# check_and_exit_if_suppressed
# ---------------------------------------------------------------------------

def test_check_does_not_exit_when_allowed(capsys):
    cfg = NotifyWindowConfig(windows=["00:00-23:59"])
    check_and_exit_if_suppressed(cfg, now=_dt(12, 0))
    captured = capsys.readouterr()
    assert "allowed" in captured.out


def test_check_exits_when_suppressed(capsys):
    cfg = NotifyWindowConfig(windows=["09:00-17:00"])
    with pytest.raises(SystemExit) as exc_info:
        check_and_exit_if_suppressed(cfg, now=_dt(3, 0), exit_code=2)
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "suppressed" in captured.out


def test_check_disabled_never_exits(capsys):
    cfg = NotifyWindowConfig(enabled=False, windows=["09:00-17:00"])
    check_and_exit_if_suppressed(cfg, now=_dt(3, 0))
    captured = capsys.readouterr()
    assert "allowed" in captured.out

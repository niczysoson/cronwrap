"""Tests for cronwrap.drift and cronwrap.cli_drift."""
from __future__ import annotations

import io
import sys
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.drift import (
    DriftConfig,
    DriftResult,
    drift_from_dict,
    measure_drift,
)
from cronwrap.cli_drift import (
    render_drift_status,
    check_and_exit_if_drifted,
)


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


# --- DriftConfig ---

def test_config_valid():
    cfg = DriftConfig(max_drift_seconds=60)
    assert cfg.max_drift_seconds == 60
    assert cfg.warn_only is True
    assert cfg.enabled is True


def test_config_invalid():
    with pytest.raises(ValueError):
        DriftConfig(max_drift_seconds=0)


def test_drift_from_dict():
    cfg = drift_from_dict({"max_drift_seconds": 120, "warn_only": False, "enabled": True})
    assert cfg.max_drift_seconds == 120
    assert cfg.warn_only is False


def test_drift_from_dict_defaults():
    cfg = drift_from_dict({})
    assert cfg.max_drift_seconds == 300
    assert cfg.warn_only is True


# --- DriftResult ---

def test_drift_seconds_positive():
    result = DriftResult(
        scheduled_at=_utc(0),
        actual_at=_utc(120),
        max_drift_seconds=300,
    )
    assert result.drift_seconds == pytest.approx(120.0)
    assert not result.exceeded


def test_drift_exceeded():
    result = DriftResult(
        scheduled_at=_utc(0),
        actual_at=_utc(400),
        max_drift_seconds=300,
    )
    assert result.exceeded
    assert "EXCEEDED" in result.summary()


def test_drift_ok_summary():
    result = DriftResult(
        scheduled_at=_utc(0),
        actual_at=_utc(10),
        max_drift_seconds=300,
    )
    assert "ok" in result.summary()


# --- measure_drift ---

def test_measure_drift_uses_provided_actual():
    cfg = DriftConfig(max_drift_seconds=60)
    result = measure_drift(cfg, _utc(0), _utc(30))
    assert result.drift_seconds == pytest.approx(30.0)


# --- render_drift_status ---

def test_render_drift_status_contains_key_fields():
    result = DriftResult(
        scheduled_at=_utc(0),
        actual_at=_utc(200),
        max_drift_seconds=100,
    )
    text = render_drift_status(result)
    assert "Drift" in text
    assert "EXCEEDED" in text


# --- check_and_exit_if_drifted ---

def test_check_no_exit_when_disabled():
    cfg = DriftConfig(max_drift_seconds=10, enabled=False)
    result = check_and_exit_if_drifted(cfg, _utc(0), _utc(999))
    assert result is None


def test_check_warn_only_does_not_exit(capsys):
    cfg = DriftConfig(max_drift_seconds=10, warn_only=True)
    buf = io.StringIO()
    result = check_and_exit_if_drifted(cfg, _utc(0), _utc(999), out=buf)
    assert result is not None
    assert result.exceeded
    assert "EXCEEDED" in buf.getvalue()


def test_check_exits_when_warn_only_false():
    cfg = DriftConfig(max_drift_seconds=10, warn_only=False)
    buf = io.StringIO()
    with pytest.raises(SystemExit) as exc_info:
        check_and_exit_if_drifted(cfg, _utc(0), _utc(999), out=buf)
    assert exc_info.value.code == 1


def test_check_no_exit_within_limit():
    cfg = DriftConfig(max_drift_seconds=300, warn_only=False)
    buf = io.StringIO()
    result = check_and_exit_if_drifted(cfg, _utc(0), _utc(10), out=buf)
    assert result is not None
    assert not result.exceeded
    assert buf.getvalue() == ""

"""Tests for cronwrap.grace and cronwrap.cli_grace."""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwrap.grace import (
    GraceConfig,
    GraceResult,
    check_grace,
    grace_from_dict,
)
from cronwrap.cli_grace import render_grace_status, check_and_exit_if_in_grace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(started_at: datetime):
    entry = MagicMock()
    entry.started_at = started_at
    return entry


def _mock_history(entries):
    h = MagicMock()
    h.for_job.return_value = entries
    return h


# ---------------------------------------------------------------------------
# GraceConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = GraceConfig(enabled=True, grace_seconds=120, job_name="backup")
    assert cfg.grace_seconds == 120


def test_config_invalid_grace_seconds():
    with pytest.raises(ValueError):
        GraceConfig(grace_seconds=-1)


def test_config_invalid_enabled_type():
    with pytest.raises(TypeError):
        GraceConfig(enabled="yes")  # type: ignore[arg-type]


def test_grace_from_dict():
    cfg = grace_from_dict({"enabled": True, "grace_seconds": 60, "job_name": "sync"})
    assert cfg.grace_seconds == 60
    assert cfg.job_name == "sync"


def test_grace_from_dict_defaults():
    cfg = grace_from_dict({})
    assert cfg.enabled is True
    assert cfg.grace_seconds == 300


# ---------------------------------------------------------------------------
# check_grace
# ---------------------------------------------------------------------------

def test_disabled_never_in_grace():
    cfg = GraceConfig(enabled=False, grace_seconds=3600, job_name="job")
    history = _mock_history([])
    result = check_grace(cfg, history)
    assert result.in_grace is False


def test_no_history_is_in_grace():
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    history = _mock_history([])
    result = check_grace(cfg, history)
    assert result.in_grace is True
    assert result.first_run_at is None


def test_within_grace_window():
    now = datetime.now(timezone.utc)
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    entries = [_make_entry(now - timedelta(seconds=60))]
    result = check_grace(cfg, _mock_history(entries))
    assert result.in_grace is True
    assert result.elapsed_seconds is not None
    assert result.elapsed_seconds < 300


def test_outside_grace_window():
    now = datetime.now(timezone.utc)
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    entries = [_make_entry(now - timedelta(seconds=400))]
    result = check_grace(cfg, _mock_history(entries))
    assert result.in_grace is False


def test_uses_earliest_entry_as_first_run():
    now = datetime.now(timezone.utc)
    cfg = GraceConfig(enabled=True, grace_seconds=600, job_name="job")
    entries = [
        _make_entry(now - timedelta(seconds=100)),
        _make_entry(now - timedelta(seconds=500)),
    ]
    result = check_grace(cfg, _mock_history(entries))
    assert result.elapsed_seconds is not None
    assert result.elapsed_seconds >= 500


# ---------------------------------------------------------------------------
# render_grace_status
# ---------------------------------------------------------------------------

def test_render_active():
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    result = GraceResult(
        in_grace=True,
        grace_seconds=300,
        first_run_at=None,
        elapsed_seconds=None,
    )
    output = render_grace_status(cfg, result)
    assert "ACTIVE" in output
    assert "⏳" in output


def test_render_expired():
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    result = GraceResult(
        in_grace=False,
        grace_seconds=300,
        first_run_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        elapsed_seconds=400.0,
    )
    output = render_grace_status(cfg, result)
    assert "EXPIRED" in output
    assert "✓" in output


# ---------------------------------------------------------------------------
# check_and_exit_if_in_grace
# ---------------------------------------------------------------------------

def test_exits_when_in_grace(capsys):
    cfg = GraceConfig(enabled=True, grace_seconds=300, job_name="job")
    history = _mock_history([])
    with pytest.raises(SystemExit) as exc_info:
        check_and_exit_if_in_grace(cfg, history, suppress_failures=True)
    assert exc_info.value.code == 0


def test_no_exit_when_not_in_grace():
    now = datetime.now(timezone.utc)
    cfg = GraceConfig(enabled=True, grace_seconds=10, job_name="job")
    entries = [_make_entry(now - timedelta(seconds=60))]
    history = _mock_history(entries)
    result = check_and_exit_if_in_grace(cfg, history, suppress_failures=True)
    assert result.in_grace is False

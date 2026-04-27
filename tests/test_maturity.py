"""Tests for cronwrap.maturity and cronwrap.cli_maturity."""
from __future__ import annotations

import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from cronwrap.maturity import (
    MaturityConfig,
    MaturityResult,
    maturity_from_dict,
    check_maturity,
)
from cronwrap.cli_maturity import render_maturity_result, check_and_exit_if_stale
from cronwrap.history import JobHistory, HistoryEntry


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(job_name: str, hours_ago: float, success: bool = True) -> HistoryEntry:
    started = datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)
    return HistoryEntry(
        job_name=job_name,
        started_at=started,
        finished_at=started + timedelta(seconds=10),
        exit_code=0 if success else 1,
        stdout="",
        stderr="",
    )


def _mock_history(entries):
    h = MagicMock(spec=JobHistory)
    h.for_job.return_value = entries
    return h


# ---------------------------------------------------------------------------
# MaturityConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = MaturityConfig(max_age_hours=24.0, job_name="backup")
    assert cfg.max_age_hours == 24.0
    assert cfg.enabled is True


def test_config_invalid_age():
    with pytest.raises(ValueError, match="max_age_hours"):
        MaturityConfig(max_age_hours=0, job_name="backup")


def test_config_invalid_job_name():
    with pytest.raises(ValueError, match="job_name"):
        MaturityConfig(max_age_hours=1.0, job_name="  ")


def test_maturity_from_dict():
    cfg = maturity_from_dict({"max_age_hours": 6.0, "job_name": "sync", "enabled": False})
    assert cfg.max_age_hours == 6.0
    assert cfg.job_name == "sync"
    assert cfg.enabled is False


# ---------------------------------------------------------------------------
# check_maturity
# ---------------------------------------------------------------------------

def test_no_history_is_stale():
    cfg = MaturityConfig(max_age_hours=24.0, job_name="backup")
    h = _mock_history([])
    result = check_maturity(cfg, h)
    assert result.is_mature is True
    assert result.last_success is None
    assert result.age_hours is None


def test_recent_success_is_ok():
    cfg = MaturityConfig(max_age_hours=24.0, job_name="backup")
    h = _mock_history([_entry("backup", hours_ago=1.0)])
    result = check_maturity(cfg, h)
    assert result.is_mature is False
    assert result.age_hours is not None
    assert result.age_hours < 24.0


def test_old_success_is_stale():
    cfg = MaturityConfig(max_age_hours=6.0, job_name="backup")
    h = _mock_history([_entry("backup", hours_ago=10.0)])
    result = check_maturity(cfg, h)
    assert result.is_mature is True


def test_only_failures_is_stale():
    cfg = MaturityConfig(max_age_hours=24.0, job_name="backup")
    h = _mock_history([_entry("backup", hours_ago=1.0, success=False)])
    result = check_maturity(cfg, h)
    assert result.is_mature is True


def test_disabled_never_stale():
    cfg = MaturityConfig(max_age_hours=1.0, job_name="backup", enabled=False)
    h = _mock_history([])
    result = check_maturity(cfg, h)
    assert result.is_mature is False


# ---------------------------------------------------------------------------
# summary / rendering
# ---------------------------------------------------------------------------

def test_summary_ok():
    r = MaturityResult(job_name="j", last_success=None, age_hours=2.0,
                       is_mature=False, threshold_hours=24.0)
    assert "OK" in r.summary()


def test_summary_stale_no_history():
    r = MaturityResult(job_name="j", last_success=None, age_hours=None,
                       is_mature=True, threshold_hours=24.0)
    assert "never" in r.summary()


def test_render_contains_job_name():
    r = MaturityResult(job_name="myjob", last_success=None, age_hours=5.0,
                       is_mature=False, threshold_hours=24.0)
    rendered = render_maturity_result(r)
    assert "myjob" in rendered


def test_check_and_exit_if_stale_exits(capsys):
    cfg = MaturityConfig(max_age_hours=1.0, job_name="j")
    h = _mock_history([])
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_stale(cfg, h)
    assert exc.value.code == 1


def test_check_and_exit_ok_returns_result(capsys):
    cfg = MaturityConfig(max_age_hours=24.0, job_name="j")
    h = _mock_history([_entry("j", hours_ago=1.0)])
    result = check_and_exit_if_stale(cfg, h)
    assert result.is_mature is False

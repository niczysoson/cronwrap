"""Tests for cronwrap.quota and cronwrap.cli_quota."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cronwrap.quota import (
    QuotaConfig,
    quota_from_dict,
    count_runs_in_window,
    is_quota_exceeded,
    quota_status,
)
from cronwrap.cli_quota import render_quota_status, check_and_exit_if_quota_exceeded


def _entry(offset_seconds: int = 0):
    e = MagicMock()
    e.started_at = datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)
    return e


def _store(entries):
    store = MagicMock()
    store.get.return_value = entries
    store.all.return_value = entries
    return store


# --- QuotaConfig ---

def test_config_valid():
    cfg = QuotaConfig(max_runs=5, window_seconds=3600, job_name="backup")
    assert cfg.max_runs == 5


def test_config_invalid_max_runs():
    with pytest.raises(ValueError):
        QuotaConfig(max_runs=0, window_seconds=60)


def test_config_invalid_window():
    with pytest.raises(ValueError):
        QuotaConfig(max_runs=1, window_seconds=0)


def test_quota_from_dict():
    cfg = quota_from_dict({"max_runs": "3", "window_seconds": "600", "job_name": "sync"})
    assert cfg.max_runs == 3 and cfg.window_seconds == 600


# --- count_runs_in_window ---

def test_count_runs_all_recent():
    entries = [_entry(10), _entry(20), _entry(30)]
    assert count_runs_in_window(entries, 60) == 3


def test_count_runs_some_old():
    entries = [_entry(10), _entry(200)]
    assert count_runs_in_window(entries, 60) == 1


# --- is_quota_exceeded ---

def test_not_exceeded():
    cfg = QuotaConfig(max_runs=5, window_seconds=3600, job_name="j")
    assert not is_quota_exceeded(cfg, _store([_entry(10), _entry(20)]))


def test_exceeded():
    cfg = QuotaConfig(max_runs=2, window_seconds=3600, job_name="j")
    assert is_quota_exceeded(cfg, _store([_entry(10), _entry(20)]))


# --- quota_status ---

def test_quota_status_fields():
    cfg = QuotaConfig(max_runs=3, window_seconds=300, job_name="j")
    s = quota_status(cfg, _store([_entry(5)]))
    assert s["runs_in_window"] == 1
    assert s["remaining"] == 2
    assert not s["exceeded"]


# --- CLI ---

def test_render_quota_status_ok():
    cfg = QuotaConfig(max_runs=10, window_seconds=3600, job_name="j")
    out = render_quota_status(cfg, _store([]))
    assert "OK" in out and "10" in out


def test_check_exits_when_exceeded(capsys):
    cfg = QuotaConfig(max_runs=1, window_seconds=3600, job_name="j")
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_quota_exceeded(cfg, _store([_entry(5)]))
    assert exc.value.code == 1


def test_check_no_exit_when_ok(capsys):
    cfg = QuotaConfig(max_runs=5, window_seconds=3600, job_name="j")
    check_and_exit_if_quota_exceeded(cfg, _store([_entry(5)]))

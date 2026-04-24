"""Tests for cronwrap.variance and cronwrap.cli_variance."""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cronwrap.variance import VarianceReport, compute_variance, compute_all_variance
from cronwrap.cli_variance import render_variance_report, render_variance_table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(job_name: str, duration_seconds: float, success: bool = True):
    """Return a minimal mock HistoryEntry."""
    now = datetime(2024, 1, 1, 12, 0, 0)
    e = MagicMock()
    e.job_name = job_name
    e.started_at = now
    e.finished_at = now + timedelta(seconds=duration_seconds)
    e.exit_code = 0 if success else 1
    return e


def _mock_history(entries):
    h = MagicMock()
    h.all.return_value = entries
    h.for_job.side_effect = lambda name: [e for e in entries if e.job_name == name]
    return h


# ---------------------------------------------------------------------------
# compute_variance
# ---------------------------------------------------------------------------

def test_empty_history_returns_none_stats():
    h = _mock_history([])
    r = compute_variance("backup", h)
    assert r.sample_count == 0
    assert r.mean_seconds is None
    assert r.stddev_seconds is None
    assert r.cv_percent is None
    assert r.is_stable is True  # no data → treated as stable


def test_single_entry_returns_zero_stddev():
    h = _mock_history([_make_entry("backup", 30.0)])
    r = compute_variance("backup", h)
    assert r.sample_count == 1
    assert r.mean_seconds == pytest.approx(30.0)
    assert r.stddev_seconds == pytest.approx(0.0)
    assert r.cv_percent == pytest.approx(0.0)
    assert r.is_stable is True


def test_consistent_durations_are_stable():
    entries = [_make_entry("sync", 10.0) for _ in range(5)]
    h = _mock_history(entries)
    r = compute_variance("sync", h)
    assert r.cv_percent == pytest.approx(0.0)
    assert r.is_stable is True


def test_high_variance_marked_unstable():
    # durations: 1 s and 100 s — very high CV
    entries = [_make_entry("flaky", 1.0), _make_entry("flaky", 100.0)]
    h = _mock_history(entries)
    r = compute_variance("flaky", h)
    assert r.is_stable is False
    assert r.cv_percent is not None and r.cv_percent > 25.0


def test_to_dict_contains_all_keys():
    h = _mock_history([_make_entry("job", 5.0)])
    r = compute_variance("job", h)
    d = r.to_dict()
    for key in ("job_name", "sample_count", "mean_seconds", "stddev_seconds",
                "min_seconds", "max_seconds", "cv_percent", "is_stable"):
        assert key in d


# ---------------------------------------------------------------------------
# compute_all_variance
# ---------------------------------------------------------------------------

def test_compute_all_variance_multiple_jobs():
    entries = [
        _make_entry("alpha", 10.0),
        _make_entry("beta", 20.0),
        _make_entry("alpha", 12.0),
    ]
    h = _mock_history(entries)
    reports = compute_all_variance(h)
    names = [r.job_name for r in reports]
    assert "alpha" in names
    assert "beta" in names


# ---------------------------------------------------------------------------
# CLI rendering
# ---------------------------------------------------------------------------

def test_render_variance_report_stable():
    r = VarianceReport("myjob", 3, 10.0, 0.5, 9.5, 10.5, 5.0)
    out = render_variance_report(r)
    assert "myjob" in out
    assert "stable" in out.lower()
    assert "5.0%" in out


def test_render_variance_report_unstable():
    r = VarianceReport("badJob", 2, 50.0, 40.0, 10.0, 90.0, 80.0)
    out = render_variance_report(r)
    assert "UNSTABLE" in out


def test_render_variance_table_empty():
    out = render_variance_table([])
    assert "No variance" in out


def test_render_variance_table_contains_job_names():
    reports = [
        VarianceReport("alpha", 5, 10.0, 1.0, 9.0, 11.0, 10.0),
        VarianceReport("beta", 2, 30.0, 0.0, 30.0, 30.0, 0.0),
    ]
    out = render_variance_table(reports)
    assert "alpha" in out
    assert "beta" in out
    assert "yes" in out  # beta is stable

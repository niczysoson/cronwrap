"""Tests for cronwrap.profiler and cronwrap.cli_profiler."""
import time
from unittest.mock import patch

import pytest

from cronwrap.profiler import ProfileSample, Profiler, profiler_from_dict
from cronwrap.cli_profiler import (
    _fmt_seconds,
    _fmt_kb,
    render_profile_sample,
    render_profile_table,
)


# ── ProfileSample ────────────────────────────────────────────────────────────

def test_wall_seconds_none_before_finish():
    s = ProfileSample(job_name="job", started_at=1000.0)
    assert s.wall_seconds is None


def test_wall_seconds_computed():
    s = ProfileSample(job_name="job", started_at=1000.0, finished_at=1005.5)
    assert abs(s.wall_seconds - 5.5) < 1e-9


def test_round_trip_dict():
    s = ProfileSample(
        job_name="myjob",
        started_at=100.0,
        finished_at=105.0,
        user_cpu_seconds=1.2,
        system_cpu_seconds=0.3,
        max_rss_kb=4096,
    )
    d = s.to_dict()
    s2 = ProfileSample.from_dict(d)
    assert s2.job_name == "myjob"
    assert s2.finished_at == 105.0
    assert s2.user_cpu_seconds == 1.2
    assert s2.max_rss_kb == 4096


# ── Profiler context manager ──────────────────────────────────────────────────

def test_profiler_captures_wall_time():
    p = Profiler("slowjob")
    with p:
        time.sleep(0.05)
    assert p.sample is not None
    assert p.sample.wall_seconds is not None
    assert p.sample.wall_seconds >= 0.04


def test_profiler_sample_is_none_before_use():
    p = Profiler("job")
    assert p.sample is None


def test_profiler_from_dict():
    p = profiler_from_dict({"job_name": "backup"})
    assert isinstance(p, Profiler)
    assert p.job_name == "backup"


# ── CLI helpers ───────────────────────────────────────────────────────────────

def test_fmt_seconds_milliseconds():
    assert "ms" in _fmt_seconds(0.25)


def test_fmt_seconds_full_seconds():
    result = _fmt_seconds(3.5)
    assert "s" in result
    assert "ms" not in result


def test_fmt_seconds_none():
    assert _fmt_seconds(None) == "—"


def test_fmt_kb_under_1024():
    assert _fmt_kb(512) == "512 KB"


def test_fmt_kb_over_1024():
    assert "MB" in _fmt_kb(2048)


def test_render_profile_sample_contains_job_name():
    s = ProfileSample("myjob", 0.0, 1.0, 0.5, 0.1, 1024)
    line = render_profile_sample(s)
    assert "myjob" in line
    assert "wall=" in line


def test_render_profile_table_empty():
    assert "No profile" in render_profile_table([])


def test_render_profile_table_has_header():
    s = ProfileSample("job1", 0.0, 2.0, 1.0, 0.2, 8192)
    table = render_profile_table([s])
    assert "Job" in table
    assert "job1" in table

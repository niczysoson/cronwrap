"""Tests for the dashboard rendering module."""
from datetime import datetime
from cronwrap.history import JobHistory, HistoryEntry
from cronwrap.dashboard import render_job_summary, render_all_jobs


def _make_entry(job: str, success: bool, exit_code: int = 0, offset_seconds: int = 0) -> HistoryEntry:
    return HistoryEntry(
        job_name=job,
        started_at=datetime(2024, 1, 15, 10, offset_seconds % 60),
        duration_seconds=1.5 + offset_seconds,
        exit_code=exit_code,
        success=success,
    )


def test_render_job_summary_no_history():
    h = JobHistory()
    output = render_job_summary(h, "missing-job")
    assert "No history found" in output
    assert "missing-job" in output


def test_render_job_summary_with_entries():
    h = JobHistory()
    h.record(_make_entry("backup", True, 0, 0))
    h.record(_make_entry("backup", False, 1, 1))
    h.record(_make_entry("backup", True, 0, 2))
    output = render_job_summary(h, "backup")
    assert "backup" in output
    assert "2/3" in output
    assert "✓" in output
    assert "✗" in output


def test_render_job_summary_limit():
    h = JobHistory()
    for i in range(20):
        h.record(_make_entry("nightly", i % 2 == 0, offset_seconds=i))
    output = render_job_summary(h, "nightly", limit=5)
    assert "Last 5 runs" in output


def test_render_all_jobs_empty():
    h = JobHistory()
    output = render_all_jobs(h)
    assert "No job history" in output


def test_render_all_jobs_multiple():
    h = JobHistory()
    h.record(_make_entry("job-a", True))
    h.record(_make_entry("job-b", False, exit_code=2))
    h.record(_make_entry("job-a", True))
    output = render_all_jobs(h)
    assert "job-a" in output
    assert "job-b" in output
    assert "100%" in output
    assert "0%" in output

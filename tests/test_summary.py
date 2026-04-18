"""Tests for cronwrap.summary."""
import pytest
from cronwrap.history import HistoryEntry
from cronwrap.summary import summarise, summarise_all, render_summary_table


def _entry(name: str, succeeded: bool, duration: float = 1.0, started: str = "2024-01-01T00:00:00") -> HistoryEntry:
    return HistoryEntry(
        job_name=name,
        started_at=started,
        duration_seconds=duration,
        exit_code=0 if succeeded else 1,
        stdout="",
        stderr="",
    )


def test_summarise_no_entries():
    s = summarise("missing", [])
    assert s.total_runs == 0
    assert s.success_rate == 0.0
    assert s.last_status is None


def test_summarise_all_success():
    entries = [_entry("backup", True, 2.0), _entry("backup", True, 4.0)]
    s = summarise("backup", entries)
    assert s.total_runs == 2
    assert s.success_rate == 1.0
    assert s.avg_duration == pytest.approx(3.0)
    assert s.last_status == "success"


def test_summarise_mixed():
    entries = [_entry("job", True), _entry("job", False), _entry("job", True)]
    s = summarise("job", entries)
    assert s.total_runs == 3
    assert s.success_rate == pytest.approx(2 / 3)
    assert s.last_status in ("success", "failure")


def test_summarise_filters_by_name():
    entries = [_entry("a", True), _entry("b", False)]
    s = summarise("a", entries)
    assert s.total_runs == 1
    assert s.success_rate == 1.0


def test_summarise_all_groups_correctly():
    entries = [
        _entry("alpha", True),
        _entry("beta", False),
        _entry("alpha", False),
    ]
    summaries = summarise_all(entries)
    names = [s.job_name for s in summaries]
    assert "alpha" in names and "beta" in names
    alpha = next(s for s in summaries if s.job_name == "alpha")
    assert alpha.total_runs == 2


def test_render_summary_table_empty():
    result = render_summary_table([])
    assert "No job history" in result


def test_render_summary_table_contains_job_name():
    entries = [_entry("nightly", True, 5.0)]
    summaries = summarise_all(entries)
    table = render_summary_table(summaries)
    assert "nightly" in table
    assert "100.0%" in table


def test_to_dict_keys():
    s = summarise("x", [_entry("x", True, 3.0)])
    d = s.to_dict()
    assert set(d.keys()) == {"job_name", "total_runs", "success_rate", "avg_duration_seconds", "last_status", "last_ran"}

"""Tests for cronwrap.metrics and cronwrap.export."""
import json
from pathlib import Path

import pytest

from cronwrap.history import HistoryEntry, JobHistory
from cronwrap.metrics import JobMetrics, compute_metrics, compute_all_metrics
from cronwrap.export import to_json, to_text, write_json, write_text


def _entry(name: str, success: bool, duration: float) -> HistoryEntry:
    return HistoryEntry(
        job_name=name,
        started_at="2024-01-01T00:00:00",
        duration_seconds=duration,
        success=success,
        exit_code=0 if success else 1,
        stdout="",
        stderr="",
    )


@pytest.fixture()
def history(tmp_path):
    h = JobHistory(tmp_path / "hist.json")
    h._entries = [
        _entry("backup", True, 10.0),
        _entry("backup", False, 5.0),
        _entry("backup", True, 15.0),
        _entry("sync", True, 3.0),
    ]
    return h


def test_compute_metrics_basic(history):
    m = compute_metrics("backup", history)
    assert m.total_runs == 3
    assert m.successful_runs == 2
    assert m.failed_runs == 1
    assert abs(m.success_rate - 2 / 3) < 1e-6
    assert m.min_duration_seconds == 5.0
    assert m.max_duration_seconds == 15.0
    assert abs(m.avg_duration_seconds - 10.0) < 1e-6


def test_compute_metrics_empty(history):
    m = compute_metrics("nonexistent", history)
    assert m.total_runs == 0
    assert m.success_rate == 0.0
    assert m.avg_duration_seconds == 0.0


def test_compute_all_metrics(history):
    all_m = compute_all_metrics(history)
    names = {m.job_name for m in all_m}
    assert names == {"backup", "sync"}


def test_to_json(history):
    all_m = compute_all_metrics(history)
    out = to_json(all_m)
    data = json.loads(out)
    assert isinstance(data, list)
    assert any(d["job_name"] == "backup" for d in data)


def test_to_text_no_metrics():
    assert to_text([]) == "No metrics available."


def test_to_text_with_metrics(history):
    all_m = compute_all_metrics(history)
    text = to_text(all_m)
    assert "backup" in text
    assert "sync" in text


def test_write_json(tmp_path, history):
    out = tmp_path / "metrics.json"
    write_json(compute_all_metrics(history), out)
    data = json.loads(out.read_text())
    assert len(data) == 2


def test_write_text(tmp_path, history):
    out = tmp_path / "metrics.txt"
    write_text(compute_all_metrics(history), out)
    assert "backup" in out.read_text()

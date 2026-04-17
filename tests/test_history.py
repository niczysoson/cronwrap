"""Tests for cronwrap.history module."""

import json
import os
import tempfile

import pytest

from cronwrap.history import HistoryEntry, JobHistory


def _make_entry(job_name="test-job", exit_code=0, attempts=1) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        command="echo hello",
        started_at="2024-01-01T00:00:00+00:00",
        finished_at="2024-01-01T00:00:01+00:00",
        exit_code=exit_code,
        attempts=attempts,
        stdout="hello\n",
        stderr="",
    )


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "history.json")


def test_record_and_retrieve(history_file):
    h = JobHistory(history_file)
    entry = _make_entry()
    h.record(entry)
    assert len(h.all()) == 1
    assert h.last("test-job").exit_code == 0


def test_persists_to_disk(history_file):
    h = JobHistory(history_file)
    h.record(_make_entry())
    h2 = JobHistory(history_file)
    assert len(h2.all()) == 1


def test_filter_by_job_name(history_file):
    h = JobHistory(history_file)
    h.record(_make_entry(job_name="job-a"))
    h.record(_make_entry(job_name="job-b"))
    assert len(h.all("job-a")) == 1
    assert h.all("job-a")[0].job_name == "job-a"


def test_last_returns_none_for_unknown_job(history_file):
    h = JobHistory(history_file)
    assert h.last("nonexistent") is None


def test_recent_failures(history_file):
    h = JobHistory(history_file)
    h.record(_make_entry(exit_code=0))
    h.record(_make_entry(exit_code=1))
    h.record(_make_entry(exit_code=1))
    failures = h.recent_failures("test-job")
    assert len(failures) == 2
    assert all(not e.success for e in failures)


def test_success_property():
    assert _make_entry(exit_code=0).success is True
    assert _make_entry(exit_code=1).success is False


def test_corrupted_file_handled_gracefully(history_file):
    with open(history_file, "w") as f:
        f.write("not valid json")
    h = JobHistory(history_file)
    assert h.all() == []

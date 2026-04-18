"""Tests for cronwrap.tags module."""
import json
import os
import pytest
from cronwrap.history import JobHistory, HistoryEntry
from cronwrap import tags as tag_module


@pytest.fixture
def history_file(tmp_path):
    p = tmp_path / "history.json"
    return str(p)


@pytest.fixture
def populated_history(history_file):
    h = JobHistory(history_file)
    h.record(HistoryEntry("backup", "2024-01-01T00:00:00", 1.0, 0, tags=["daily", "db"]))
    h.record(HistoryEntry("cleanup", "2024-01-01T01:00:00", 0.5, 0, tags=["daily"]))
    h.record(HistoryEntry("report", "2024-01-01T02:00:00", 2.0, 1, tags=["weekly", "db"]))
    h.record(HistoryEntry("backup", "2024-01-02T00:00:00", 1.2, 0, tags=["daily", "db"]))
    return h


def test_get_jobs_by_tag_daily(populated_history):
    result = tag_module.get_jobs_by_tag(populated_history, "daily")
    assert result == ["backup", "cleanup"]


def test_get_jobs_by_tag_db(populated_history):
    result = tag_module.get_jobs_by_tag(populated_history, "db")
    assert result == ["backup", "report"]


def test_get_jobs_by_tag_missing(populated_history):
    result = tag_module.get_jobs_by_tag(populated_history, "nonexistent")
    assert result == []


def test_group_by_tag(populated_history):
    groups = tag_module.group_by_tag(populated_history)
    assert set(groups.keys()) == {"daily", "db", "weekly"}
    assert groups["daily"] == ["backup", "cleanup"]
    assert groups["db"] == ["backup", "report"]
    assert groups["weekly"] == ["report"]


def test_filter_entries_by_tag(populated_history):
    entries = tag_module.filter_entries_by_tag(populated_history, "weekly")
    assert len(entries) == 1
    assert entries[0].job_name == "report"


def test_filter_entries_by_tag_multiple(populated_history):
    entries = tag_module.filter_entries_by_tag(populated_history, "daily")
    assert len(entries) == 3
    names = [e.job_name for e in entries]
    assert names.count("backup") == 2
    assert names.count("cleanup") == 1

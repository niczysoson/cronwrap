"""Tests for cronwrap.watermark."""
import json
import os
import pytest

from cronwrap.watermark import WatermarkEntry, WatermarkStore


@pytest.fixture
def store(tmp_path):
    return WatermarkStore(str(tmp_path / "watermarks.json"))


def test_get_missing_returns_none(store):
    assert store.get("backup") is None


def test_update_creates_entry(store):
    updated = store.update("backup", 10.5, 2048)
    assert updated is True
    entry = store.get("backup")
    assert entry is not None
    assert entry.peak_duration_seconds == 10.5
    assert entry.peak_output_bytes == 2048


def test_update_replaces_when_higher(store):
    store.update("backup", 10.0, 1000)
    updated = store.update("backup", 20.0, 500)
    assert updated is True
    entry = store.get("backup")
    assert entry.peak_duration_seconds == 20.0
    assert entry.peak_output_bytes == 1000  # not replaced — lower


def test_update_no_change_when_lower(store):
    store.update("backup", 10.0, 1000)
    updated = store.update("backup", 5.0, 500)
    assert updated is False
    entry = store.get("backup")
    assert entry.peak_duration_seconds == 10.0
    assert entry.peak_output_bytes == 1000


def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "wm.json")
    s1 = WatermarkStore(path)
    s1.update("deploy", 30.0, 4096)
    s2 = WatermarkStore(path)
    entry = s2.get("deploy")
    assert entry is not None
    assert entry.peak_duration_seconds == 30.0


def test_all_returns_all_entries(store):
    store.update("job_a", 1.0, 100)
    store.update("job_b", 2.0, 200)
    names = {e.job_name for e in store.all()}
    assert names == {"job_a", "job_b"}


def test_reset_removes_entry(store):
    store.update("cleanup", 5.0, 512)
    removed = store.reset("cleanup")
    assert removed is True
    assert store.get("cleanup") is None


def test_reset_missing_returns_false(store):
    assert store.reset("nonexistent") is False


def test_round_trip_dict():
    entry = WatermarkEntry("myjob", 12.3, 999, "2024-01-01T00:00:00+00:00")
    restored = WatermarkEntry.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.peak_duration_seconds == entry.peak_duration_seconds
    assert restored.peak_output_bytes == entry.peak_output_bytes

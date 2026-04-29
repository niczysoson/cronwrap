"""Tests for cronwrap.pauselist."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.pauselist import PauseEntry, PauseStore

UTC = timezone.utc
NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "pauses.json"


@pytest.fixture()
def store(store_path: Path) -> PauseStore:
    return PauseStore(str(store_path))


def _entry(
    job: str = "backup",
    reason: str = "maintenance",
    resume_at: datetime | None = None,
) -> PauseEntry:
    return PauseEntry(
        job_name=job,
        paused_at=NOW,
        reason=reason,
        resume_at=resume_at,
    )


# --- PauseEntry ---

def test_entry_active_indefinite():
    e = _entry()
    assert e.is_active(NOW) is True
    assert e.is_active(NOW + timedelta(days=365)) is True


def test_entry_active_before_resume_at():
    e = _entry(resume_at=NOW + timedelta(hours=2))
    assert e.is_active(NOW + timedelta(hours=1)) is True


def test_entry_inactive_after_resume_at():
    e = _entry(resume_at=NOW + timedelta(hours=2))
    assert e.is_active(NOW + timedelta(hours=3)) is False


def test_entry_round_trip():
    e = _entry(resume_at=NOW + timedelta(hours=1))
    assert PauseEntry.from_dict(e.to_dict()).job_name == e.job_name
    assert PauseEntry.from_dict(e.to_dict()).resume_at == e.resume_at


def test_entry_round_trip_no_resume():
    e = _entry()
    restored = PauseEntry.from_dict(e.to_dict())
    assert restored.resume_at is None
    assert restored.reason == "maintenance"


# --- PauseStore ---

def test_store_empty_is_not_paused(store: PauseStore):
    assert store.is_paused("backup", NOW) is False


def test_store_pause_and_check(store: PauseStore):
    store.pause(_entry("backup"))
    assert store.is_paused("backup", NOW) is True


def test_store_resume_removes_pause(store: PauseStore):
    store.pause(_entry("backup"))
    store.resume("backup")
    assert store.is_paused("backup", NOW) is False


def test_store_pause_replaces_existing(store: PauseStore):
    store.pause(_entry("backup", reason="first"))
    store.pause(_entry("backup", reason="second"))
    entry = store.get("backup")
    assert entry is not None
    assert entry.reason == "second"


def test_store_timed_pause_expires(store: PauseStore):
    store.pause(_entry("backup", resume_at=NOW + timedelta(hours=1)))
    assert store.is_paused("backup", NOW + timedelta(hours=2)) is False


def test_store_all_active_filters_expired(store: PauseStore):
    store.pause(_entry("job-a", resume_at=NOW + timedelta(hours=1)))
    store.pause(_entry("job-b"))  # indefinite
    active = store.all_active(NOW + timedelta(hours=2))
    names = [e.job_name for e in active]
    assert "job-b" in names
    assert "job-a" not in names


def test_store_persists_to_disk(store: PauseStore, store_path: Path):
    store.pause(_entry("backup"))
    raw = json.loads(store_path.read_text())
    assert any(r["job_name"] == "backup" for r in raw)


def test_store_get_missing_returns_none(store: PauseStore):
    assert store.get("nonexistent") is None

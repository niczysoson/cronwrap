"""Tests for cronwrap.snapshot."""
import json
import os
import pytest
from cronwrap.snapshot import make_snapshot, SnapshotStore, _sha256


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "snapshots.json")


def test_make_snapshot_hashes():
    snap = make_snapshot("myjob", "hello", "err")
    assert snap.stdout_hash == _sha256("hello")
    assert snap.stderr_hash == _sha256("err")
    assert snap.job_name == "myjob"
    assert snap.stdout == "hello"
    assert snap.stderr == "err"


def test_snapshot_round_trip():
    snap = make_snapshot("job1", "out", "")
    restored = snap.__class__.from_dict(snap.to_dict())
    assert restored.job_name == snap.job_name
    assert restored.stdout_hash == snap.stdout_hash
    assert restored.stderr_hash == snap.stderr_hash


def test_changed_since_detects_diff():
    a = make_snapshot("j", "foo", "")
    b = make_snapshot("j", "bar", "")
    assert a.changed_since(b)


def test_changed_since_same_output():
    a = make_snapshot("j", "foo", "err")
    b = make_snapshot("j", "foo", "err")
    assert not a.changed_since(b)


def test_store_get_missing_returns_none(store_path):
    store = SnapshotStore(store_path)
    assert store.get("nonexistent") is None


def test_store_save_and_retrieve(store_path):
    store = SnapshotStore(store_path)
    snap = make_snapshot("backup", "output text", "")
    store.save(snap)
    result = store.get("backup")
    assert result is not None
    assert result.stdout == "output text"
    assert result.stdout_hash == snap.stdout_hash


def test_store_persists_to_disk(store_path):
    store = SnapshotStore(store_path)
    store.save(make_snapshot("job", "data", "warn"))
    store2 = SnapshotStore(store_path)
    assert store2.get("job") is not None


def test_store_delete(store_path):
    store = SnapshotStore(store_path)
    store.save(make_snapshot("job", "x", ""))
    store.delete("job")
    assert store.get("job") is None


def test_store_overwrite_updates_entry(store_path):
    store = SnapshotStore(store_path)
    store.save(make_snapshot("job", "v1", ""))
    store.save(make_snapshot("job", "v2", ""))
    result = store.get("job")
    assert result.stdout == "v2"

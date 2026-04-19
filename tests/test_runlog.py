"""Tests for cronwrap.runlog."""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from cronwrap.runlog import RunLog, RunLogEntry


T0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2024, 1, 1, 12, 0, 45, tzinfo=timezone.utc)


def _entry(**kwargs) -> RunLogEntry:
    defaults = dict(
        job_name="backup",
        command="tar -czf /tmp/bak.tgz /data",
        started_at=T0,
        finished_at=T1,
        exit_code=0,
        stdout="done",
        stderr="",
    )
    defaults.update(kwargs)
    return RunLogEntry(**defaults)


@pytest.fixture
def log_path(tmp_path):
    return str(tmp_path / "runlog" / "runs.json")


def test_append_and_all(log_path):
    rl = RunLog(log_path)
    e = _entry()
    rl.append(e)
    entries = rl.all()
    assert len(entries) == 1
    assert entries[0].job_name == "backup"
    assert entries[0].exit_code == 0


def test_for_job_filters(log_path):
    rl = RunLog(log_path)
    rl.append(_entry(job_name="backup"))
    rl.append(_entry(job_name="cleanup"))
    rl.append(_entry(job_name="backup"))
    assert len(rl.for_job("backup")) == 2
    assert len(rl.for_job("cleanup")) == 1


def test_last_returns_most_recent(log_path):
    rl = RunLog(log_path)
    rl.append(_entry(exit_code=1))
    rl.append(_entry(exit_code=0))
    last = rl.last("backup")
    assert last is not None
    assert last.exit_code == 0


def test_last_returns_none_for_unknown_job(log_path):
    rl = RunLog(log_path)
    assert rl.last("nonexistent") is None


def test_duration_seconds(log_path):
    e = _entry(started_at=T0, finished_at=T1)
    assert e.duration_seconds() == 45.0


def test_duration_none_if_not_finished():
    e = _entry(finished_at=None)
    assert e.duration_seconds() is None


def test_succeeded():
    assert _entry(exit_code=0).succeeded() is True
    assert _entry(exit_code=1).succeeded() is False


def test_round_trip_dict():
    e = _entry()
    restored = RunLogEntry.from_dict(e.to_dict())
    assert restored.job_name == e.job_name
    assert restored.exit_code == e.exit_code
    assert restored.started_at == e.started_at
    assert restored.finished_at == e.finished_at


def test_persists_to_disk(log_path):
    rl = RunLog(log_path)
    rl.append(_entry())
    raw = json.loads(Path(log_path).read_text())
    assert len(raw) == 1
    assert raw[0]["job_name"] == "backup"

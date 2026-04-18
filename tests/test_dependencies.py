import time
import pytest
from cronwrap.dependencies import (
    DependencyConfig,
    dependency_from_dict,
    check_dependencies,
)
from cronwrap.history import JobHistory, HistoryEntry


def _entry(job_name: str, succeeded: bool, age: float = 10.0) -> HistoryEntry:
    started = time.time() - age
    return HistoryEntry(
        job_name=job_name,
        started_at=started,
        duration_seconds=1.0,
        succeeded=succeeded,
        exit_code=0 if succeeded else 1,
        output="",
    )


def _store(tmp_path, entries):
    h = JobHistory(path=str(tmp_path / "history.json"))
    for e in entries:
        h.record(e)
    return h


def test_no_requirements_always_satisfied(tmp_path):
    h = _store(tmp_path, [])
    cfg = DependencyConfig(requires=[])
    result = check_dependencies(cfg, h)
    assert result.satisfied


def test_required_job_has_success(tmp_path):
    h = _store(tmp_path, [_entry("backup", True)])
    cfg = DependencyConfig(requires=["backup"])
    result = check_dependencies(cfg, h)
    assert result.satisfied
    assert result.missing == []


def test_required_job_only_failures(tmp_path):
    h = _store(tmp_path, [_entry("backup", False)])
    cfg = DependencyConfig(requires=["backup"])
    result = check_dependencies(cfg, h)
    assert not result.satisfied
    assert "backup" in result.missing


def test_required_job_missing_entirely(tmp_path):
    h = _store(tmp_path, [])
    cfg = DependencyConfig(requires=["ingest"])
    result = check_dependencies(cfg, h)
    assert not result.satisfied


def test_max_age_recent_success(tmp_path):
    h = _store(tmp_path, [_entry("etl", True, age=30)])
    cfg = DependencyConfig(requires=["etl"], max_age_seconds=60)
    result = check_dependencies(cfg, h)
    assert result.satisfied


def test_max_age_stale_success(tmp_path):
    h = _store(tmp_path, [_entry("etl", True, age=120)])
    cfg = DependencyConfig(requires=["etl"], max_age_seconds=60)
    result = check_dependencies(cfg, h)
    assert not result.satisfied
    assert "etl" in result.missing


def test_from_dict():
    cfg = dependency_from_dict({"requires": ["a", "b"], "max_age_seconds": 300})
    assert cfg.requires == ["a", "b"]
    assert cfg.max_age_seconds == 300


def test_invalid_max_age():
    with pytest.raises(ValueError):
        DependencyConfig(requires=[], max_age_seconds=-1)


def test_summary_messages(tmp_path):
    from cronwrap.dependencies import DependencyResult
    ok = DependencyResult(satisfied=True)
    assert "satisfied" in ok.summary()
    fail = DependencyResult(satisfied=False, missing=["x"])
    assert "x" in fail.summary()

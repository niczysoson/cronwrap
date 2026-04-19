"""Tests for cronwrap.debounce and cronwrap.cli_debounce."""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwrap.debounce import DebounceConfig, debounce_from_dict, is_debounced, elapsed_seconds
from cronwrap.cli_debounce import render_debounce_status, check_and_exit_if_debounced
from cronwrap.history import JobHistory, HistoryEntry


def _entry(job: str, seconds_ago: float) -> HistoryEntry:
    started = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return HistoryEntry(
        job_name=job,
        command="echo hi",
        started_at=started,
        finished_at=started + timedelta(seconds=1),
        exit_code=0,
        stdout="",
        stderr="",
        attempt=1,
    )


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _mock_history(history_file: Path, entries: list) -> JobHistory:
    h = JobHistory(history_file)
    for e in entries:
        h.record(e)
    return h


def test_config_valid():
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    assert cfg.cooldown_seconds == 60


def test_config_invalid_cooldown():
    with pytest.raises(ValueError):
        DebounceConfig(cooldown_seconds=0, job_name="backup")


def test_config_invalid_name():
    with pytest.raises(ValueError):
        DebounceConfig(cooldown_seconds=30, job_name="")


def test_debounce_from_dict():
    cfg = debounce_from_dict({"cooldown_seconds": "120", "job_name": "sync"})
    assert cfg.cooldown_seconds == 120
    assert cfg.job_name == "sync"


def test_not_debounced_no_history(history_file: Path):
    h = JobHistory(history_file)
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    assert not is_debounced(cfg, h)
    assert elapsed_seconds(cfg, h) is None


def test_debounced_recent_run(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=10)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    assert is_debounced(cfg, h)


def test_not_debounced_old_run(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=120)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    assert not is_debounced(cfg, h)


def test_elapsed_seconds_returns_value(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=30)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    e = elapsed_seconds(cfg, h)
    assert e is not None
    assert 28 < e < 32


def test_render_debounce_status_debounced(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=10)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    out = render_debounce_status(cfg, h)
    assert "debounced" in out
    assert "backup" in out


def test_render_debounce_status_no_history(history_file: Path):
    h = JobHistory(history_file)
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    out = render_debounce_status(cfg, h)
    assert "never" in out
    assert "not debounced" in out


def test_check_and_exit_if_debounced_exits(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=5)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_debounced(cfg, h)
    assert exc.value.code == 0


def test_check_and_exit_if_not_debounced_passes(history_file: Path):
    h = _mock_history(history_file, [_entry("backup", seconds_ago=200)])
    cfg = DebounceConfig(cooldown_seconds=60, job_name="backup")
    check_and_exit_if_debounced(cfg, h)  # should not raise

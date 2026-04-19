"""Tests for cronwrap.heartbeat and cronwrap.cli_heartbeat."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from cronwrap.heartbeat import (
    HeartbeatConfig,
    HeartbeatThread,
    heartbeat_from_dict,
    is_stale,
    read_beat,
    write_beat,
)
from cronwrap.cli_heartbeat import render_heartbeat_status, check_and_exit_if_stale


@pytest.fixture()
def cfg(tmp_path):
    return HeartbeatConfig(job_name="test_job", interval_seconds=1.0, directory=str(tmp_path), max_age_seconds=5.0)


def test_config_valid():
    cfg = HeartbeatConfig(job_name="j", interval_seconds=10.0)
    assert cfg.interval_seconds == 10.0


def test_config_invalid_interval():
    with pytest.raises(ValueError):
        HeartbeatConfig(job_name="j", interval_seconds=0)


def test_config_invalid_max_age():
    with pytest.raises(ValueError):
        HeartbeatConfig(job_name="j", max_age_seconds=-1)


def test_heartbeat_from_dict():
    cfg = heartbeat_from_dict({"job_name": "x", "interval_seconds": "15", "max_age_seconds": "60"})
    assert cfg.interval_seconds == 15.0
    assert cfg.max_age_seconds == 60.0


def test_write_and_read_beat(cfg):
    assert read_beat(cfg) is None
    write_beat(cfg)
    ts = read_beat(cfg)
    assert isinstance(ts, datetime)
    assert ts.tzinfo is not None


def test_not_stale_after_fresh_write(cfg):
    write_beat(cfg)
    assert not is_stale(cfg)


def test_stale_when_old(cfg, tmp_path):
    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=100)).isoformat()
    cfg.beat_path.write_text(json.dumps({"job": cfg.job_name, "ts": old_ts}))
    assert is_stale(cfg)


def test_stale_when_missing(cfg):
    assert is_stale(cfg)


def test_no_max_age_never_stale(tmp_path):
    cfg = HeartbeatConfig(job_name="j", directory=str(tmp_path))
    assert not is_stale(cfg)


def test_heartbeat_thread_writes(cfg):
    t = HeartbeatThread(cfg)
    t.start()
    time.sleep(0.2)
    t.stop()
    assert read_beat(cfg) is not None


def test_render_status_missing(cfg):
    out = render_heartbeat_status(cfg)
    assert "MISSING" in out


def test_render_status_ok(cfg):
    write_beat(cfg)
    out = render_heartbeat_status(cfg)
    assert "OK" in out


def test_check_and_exit_if_stale_ok(cfg):
    write_beat(cfg)
    check_and_exit_if_stale(cfg)  # should not raise


def test_check_and_exit_if_stale_exits(cfg):
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_stale(cfg)
    assert exc.value.code == 1

"""Tests for cronwrap.requeue."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from cronwrap.requeue import RequeueConfig, requeue_from_dict


@pytest.fixture()
def cfg(tmp_path: Path) -> RequeueConfig:
    return RequeueConfig(state_dir=str(tmp_path / "requeue"))


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = RequeueConfig(state_dir="/tmp/test_rq")
    assert cfg.enabled is True


def test_config_invalid_enabled():
    with pytest.raises(ValueError, match="enabled"):
        RequeueConfig(enabled="yes", state_dir="/tmp/x")  # type: ignore[arg-type]


def test_config_invalid_state_dir():
    with pytest.raises(ValueError, match="state_dir"):
        RequeueConfig(state_dir="")


def test_requeue_from_dict(tmp_path: Path):
    cfg = requeue_from_dict({"enabled": False, "state_dir": str(tmp_path)})
    assert cfg.enabled is False
    assert cfg.state_dir == str(tmp_path)


def test_requeue_from_dict_defaults():
    cfg = requeue_from_dict({})
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# is_queued / enqueue / dequeue
# ---------------------------------------------------------------------------

def test_not_queued_initially(cfg: RequeueConfig):
    assert cfg.is_queued("backup") is False


def test_enqueue_creates_sentinel(cfg: RequeueConfig):
    path = cfg.enqueue("backup", reason="manual trigger")
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["job"] == "backup"
    assert payload["reason"] == "manual trigger"
    assert "queued_at" in payload


def test_is_queued_after_enqueue(cfg: RequeueConfig):
    cfg.enqueue("report")
    assert cfg.is_queued("report") is True


def test_dequeue_returns_payload_and_removes_file(cfg: RequeueConfig):
    cfg.enqueue("sync", reason="retry")
    payload = cfg.dequeue("sync")
    assert payload is not None
    assert payload["job"] == "sync"
    assert not cfg.is_queued("sync")


def test_dequeue_returns_none_when_absent(cfg: RequeueConfig):
    result = cfg.dequeue("nonexistent")
    assert result is None


def test_disabled_config_is_never_queued(tmp_path: Path):
    cfg = RequeueConfig(enabled=False, state_dir=str(tmp_path))
    cfg.enqueue("job")  # sentinel written but is_queued ignores it
    assert cfg.is_queued("job") is False


def test_dequeue_tolerates_corrupt_file(cfg: RequeueConfig, tmp_path: Path):
    path = cfg._sentinel_path("broken")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not-json")
    result = cfg.dequeue("broken")
    assert result == {}
    assert not path.exists()

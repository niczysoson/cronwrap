"""Tests for cronwrap.checkpoint and cronwrap.cli_checkpoint."""
import pytest
from pathlib import Path

from cronwrap.checkpoint import (
    Checkpoint,
    load_checkpoint,
    save_checkpoint,
    clear_checkpoint,
)
from cronwrap.cli_checkpoint import render_checkpoint


@pytest.fixture()
def cp_dir(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


@pytest.fixture()
def saved_checkpoint(cp_dir: Path) -> Checkpoint:
    """Return a saved Checkpoint with two completed steps for reuse across tests."""
    cp = Checkpoint(job_name="etl", completed_steps=["extract", "transform"])
    save_checkpoint(cp, cp_dir)
    return cp


def test_new_checkpoint_has_no_steps():
    cp = Checkpoint(job_name="myjob")
    assert cp.completed_steps == []
    assert not cp.is_done("step1")


def test_mark_done_and_is_done():
    cp = Checkpoint(job_name="myjob")
    cp.mark_done("step1")
    assert cp.is_done("step1")
    assert not cp.is_done("step2")


def test_mark_done_idempotent():
    cp = Checkpoint(job_name="myjob")
    cp.mark_done("step1")
    cp.mark_done("step1")
    assert cp.completed_steps.count("step1") == 1


def test_round_trip_dict():
    cp = Checkpoint(job_name="j", completed_steps=["a", "b"], metadata={"k": 1})
    restored = Checkpoint.from_dict(cp.to_dict())
    assert restored.job_name == "j"
    assert restored.completed_steps == ["a", "b"]
    assert restored.metadata == {"k": 1}


def test_load_returns_none_when_missing(cp_dir):
    assert load_checkpoint("no-such-job", cp_dir) is None


def test_save_and_load(cp_dir):
    cp = Checkpoint(job_name="backup", completed_steps=["dump"], metadata={"rows": 42})
    save_checkpoint(cp, cp_dir)
    loaded = load_checkpoint("backup", cp_dir)
    assert loaded is not None
    assert loaded.completed_steps == ["dump"]
    assert loaded.metadata["rows"] == 42


def test_clear_existing(cp_dir):
    cp = Checkpoint(job_name="job1")
    save_checkpoint(cp, cp_dir)
    assert clear_checkpoint("job1", cp_dir) is True
    assert load_checkpoint("job1", cp_dir) is None


def test_clear_missing(cp_dir):
    assert clear_checkpoint("ghost", cp_dir) is False


def test_render_no_checkpoint(cp_dir):
    out = render_checkpoint("missing", cp_dir)
    assert "No checkpoint" in out


def test_render_with_steps(cp_dir, saved_checkpoint):
    out = render_checkpoint("etl", cp_dir)
    assert "extract" in out
    assert "transform" in out
    assert "✓" in out


def test_render_with_metadata(cp_dir):
    cp = Checkpoint(job_name="etl", metadata={"env": "prod"})
    save_checkpoint(cp, cp_dir)
    out = render_checkpoint("etl", cp_dir)
    assert "env" in out
    assert "prod" in out

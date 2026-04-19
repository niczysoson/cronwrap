"""Tests for cronwrap.progress and cronwrap.cli_progress."""
import json
import time
import pytest
from pathlib import Path

from cronwrap.progress import StepProgress, JobProgress, save_progress, load_progress
from cronwrap.cli_progress import render_progress, print_progress


def test_step_progress_duration():
    s = StepProgress(name="fetch", status="done", started_at=1000.0, finished_at=1005.5)
    assert s.duration_seconds == 5.5


def test_step_progress_no_duration_if_not_finished():
    s = StepProgress(name="fetch", status="running", started_at=time.time())
    assert s.duration_seconds is None


def test_step_round_trip():
    s = StepProgress(name="build", status="done", started_at=1.0, finished_at=2.0, message="ok")
    assert StepProgress.from_dict(s.to_dict()) == s


def test_job_progress_start_and_finish():
    jp = JobProgress(job_name="deploy")
    jp.start_step("compile")
    assert jp.steps[0].status == "running"
    jp.finish_step("compile", success=True, message="done")
    assert jp.steps[0].status == "done"
    assert jp.steps[0].message == "done"


def test_job_progress_finish_failure():
    jp = JobProgress(job_name="deploy")
    jp.start_step("test")
    jp.finish_step("test", success=False, message="assertion error")
    assert jp.steps[0].status == "failed"


def test_finish_unknown_step_raises():
    jp = JobProgress(job_name="deploy")
    with pytest.raises(KeyError):
        jp.finish_step("nonexistent")


def test_job_progress_round_trip():
    jp = JobProgress(job_name="etl")
    jp.start_step("extract")
    jp.finish_step("extract")
    restored = JobProgress.from_dict(jp.to_dict())
    assert restored.job_name == "etl"
    assert restored.steps[0].name == "extract"


def test_save_and_load(tmp_path):
    path = tmp_path / "progress.json"
    jp = JobProgress(job_name="backup")
    jp.start_step("dump")
    jp.finish_step("dump")
    save_progress(jp, path)
    loaded = load_progress(path)
    assert loaded is not None
    assert loaded.job_name == "backup"
    assert loaded.steps[0].name == "dump"


def test_load_missing_returns_none(tmp_path):
    assert load_progress(tmp_path / "missing.json") is None


def test_render_progress():
    jp = JobProgress(job_name="myjob")
    jp.start_step("step1")
    jp.finish_step("step1")
    jp.start_step("step2")
    jp.finish_step("step2", success=False, message="oops")
    out = render_progress(jp)
    assert "myjob" in out
    assert "✓" in out
    assert "✗" in out
    assert "oops" in out
    assert "1/2 done" in out


def test_print_progress_missing(tmp_path, capsys):
    rc = print_progress(tmp_path / "nope.json")
    assert rc == 1
    assert "No progress file" in capsys.readouterr().out


def test_print_progress_found(tmp_path, capsys):
    path = tmp_path / "p.json"
    jp = JobProgress(job_name="j")
    jp.start_step("s")
    jp.finish_step("s")
    save_progress(jp, path)
    rc = print_progress(path)
    assert rc == 0
    assert "j" in capsys.readouterr().out

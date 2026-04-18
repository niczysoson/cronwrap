"""Tests for cronwrap.chain."""
from unittest.mock import patch

import pytest

from cronwrap.chain import ChainResult, run_chain, chain_from_dict
from cronwrap.runner import RunResult


def _make_result(cmd: str, rc: int = 0, duration: float = 0.1) -> RunResult:
    return RunResult(command=cmd, returncode=rc, stdout="ok", stderr="", duration=duration)


def _patch_run(results):
    """Return a context manager that yields successive RunResults."""
    it = iter(results)
    return patch("cronwrap.chain.run", side_effect=lambda cmd, **_: next(it))


def test_all_steps_succeed():
    results = [_make_result(c) for c in ["echo a", "echo b", "echo c"]]
    with _patch_run(results):
        cr = run_chain("myjob", ["echo a", "echo b", "echo c"])
    assert cr.succeeded
    assert cr.stopped_at is None
    assert len(cr.steps) == 3
    assert cr.failed_step is None


def test_stops_on_first_failure():
    results = [_make_result("echo a"), _make_result("bad", rc=1), _make_result("echo c")]
    with _patch_run(results):
        cr = run_chain("myjob", ["echo a", "bad", "echo c"])
    assert not cr.succeeded
    assert cr.stopped_at == 1
    assert len(cr.steps) == 2  # third step never ran
    assert cr.failed_step.returncode == 1


def test_continue_on_failure():
    results = [_make_result("a"), _make_result("b", rc=1), _make_result("c")]
    with _patch_run(results):
        cr = run_chain("myjob", ["a", "b", "c"], stop_on_failure=False)
    assert len(cr.steps) == 3
    # stopped_at is None because we never set it when stop_on_failure=False
    assert cr.stopped_at is None


def test_empty_chain():
    cr = run_chain("empty", [])
    assert cr.succeeded
    assert cr.steps == []


def test_chain_from_dict_roundtrip():
    data = {
        "job_name": "myjob",
        "stopped_at": 1,
        "steps": [
            {"command": "echo a", "returncode": 0, "stdout": "ok", "stderr": "", "duration": 0.1},
            {"command": "bad", "returncode": 1, "stdout": "", "stderr": "err", "duration": 0.2},
        ],
    }
    cr = chain_from_dict(data)
    assert cr.job_name == "myjob"
    assert cr.stopped_at == 1
    assert not cr.succeeded
    assert cr.steps[0].returncode == 0
    assert cr.steps[1].command == "bad"

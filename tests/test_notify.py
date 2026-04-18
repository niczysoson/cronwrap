"""Tests for cronwrap.notify."""

from unittest.mock import MagicMock

import pytest

from cronwrap.runner import RunResult
from cronwrap.notify import (
    NotifyConfig,
    notify_success,
    notify_failure,
    notify_retry,
    log_hook,
    _safe_call,
)


def _make_result(returncode: int = 0) -> RunResult:
    return RunResult(
        returncode=returncode,
        stdout="output",
        stderr="",
        duration=1.23,
        attempts=1,
    )


def test_notify_success_calls_hooks():
    hook = MagicMock()
    cfg = NotifyConfig(on_success=[hook])
    result = _make_result(0)
    notify_success(cfg, "myjob", result)
    hook.assert_called_once_with("myjob", result)


def test_notify_failure_calls_hooks():
    hook = MagicMock()
    cfg = NotifyConfig(on_failure=[hook])
    result = _make_result(1)
    notify_failure(cfg, "myjob", result)
    hook.assert_called_once_with("myjob", result)


def test_notify_retry_calls_hooks():
    hook = MagicMock()
    cfg = NotifyConfig(on_retry=[hook])
    result = _make_result(1)
    notify_retry(cfg, "myjob", result)
    hook.assert_called_once_with("myjob", result)


def test_multiple_hooks_all_called():
    hooks = [MagicMock(), MagicMock()]
    cfg = NotifyConfig(on_success=hooks)
    result = _make_result(0)
    notify_success(cfg, "job", result)
    for h in hooks:
        h.assert_called_once_with("job", result)


def test_safe_call_swallows_exception():
    def bad_hook(job_name, result):
        raise RuntimeError("boom")

    result = _make_result(0)
    # Should not raise
    _safe_call(bad_hook, "job", result)


def test_no_hooks_is_noop():
    cfg = NotifyConfig()
    result = _make_result(0)
    notify_success(cfg, "job", result)  # no error
    notify_failure(cfg, "job", result)
    notify_retry(cfg, "job", result)


def test_log_hook_runs_without_error():
    result = _make_result(0)
    log_hook("myjob", result)  # should not raise

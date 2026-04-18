"""Tests for cronwrap.hooks and cronwrap.cli_hooks."""
import pytest
from unittest.mock import patch, MagicMock
from cronwrap.hooks import (
    HookConfig, hook_config_from_dict, HookResult,
    run_pre_hooks, run_post_hooks, _run_hook,
)
from cronwrap.cli_hooks import render_hook_config, render_hook_results


def _ok(cmd="echo ok"):
    return HookResult(cmd, 0, "ok\n", "")


def _fail(cmd="false"):
    return HookResult(cmd, 1, "", "error")


def test_hook_config_defaults():
    cfg = HookConfig()
    assert cfg.pre == []
    assert cfg.post == []
    assert cfg.post_failure == []
    assert cfg.timeout_seconds == 30
    assert cfg.stop_on_pre_failure is True


def test_hook_config_invalid_timeout():
    with pytest.raises(ValueError):
        HookConfig(timeout_seconds=0)


def test_hook_config_from_dict():
    cfg = hook_config_from_dict({"pre": ["echo a"], "timeout_seconds": 10})
    assert cfg.pre == ["echo a"]
    assert cfg.timeout_seconds == 10


def test_run_pre_hooks_all_succeed():
    cfg = HookConfig(pre=["echo a", "echo b"])
    with patch("cronwrap.hooks._run_hook", side_effect=[_ok("echo a"), _ok("echo b")]):
        results = run_pre_hooks(cfg)
    assert len(results) == 2
    assert all(r.succeeded for r in results)


def test_run_pre_hooks_stops_on_failure():
    cfg = HookConfig(pre=["false", "echo b"], stop_on_pre_failure=True)
    with patch("cronwrap.hooks._run_hook", side_effect=[_fail("false")]):
        results = run_pre_hooks(cfg)
    assert len(results) == 1


def test_run_pre_hooks_continues_on_failure():
    cfg = HookConfig(pre=["false", "echo b"], stop_on_pre_failure=False)
    with patch("cronwrap.hooks._run_hook", side_effect=[_fail("false"), _ok("echo b")]):
        results = run_pre_hooks(cfg)
    assert len(results) == 2


def test_run_post_hooks_success():
    cfg = HookConfig(post=["echo done"], post_failure=["echo fail"])
    with patch("cronwrap.hooks._run_hook", return_value=_ok()) as m:
        results = run_post_hooks(cfg, job_succeeded=True)
    assert len(results) == 1  # post_failure not included


def test_run_post_hooks_failure_includes_extra():
    cfg = HookConfig(post=["echo done"], post_failure=["echo fail"])
    with patch("cronwrap.hooks._run_hook", return_value=_ok()) as m:
        results = run_post_hooks(cfg, job_succeeded=False)
    assert len(results) == 2


def test_render_hook_config_empty():
    out = render_hook_config(HookConfig())
    assert "(none)" in out
    assert "30s" in out


def test_render_hook_config_with_hooks():
    cfg = HookConfig(pre=["echo pre"], post=["echo post"], post_failure=["echo fail"])
    out = render_hook_config(cfg)
    assert "echo pre" in out
    assert "echo post" in out
    assert "echo fail" in out


def test_render_hook_results_empty():
    out = render_hook_results([])
    assert "no hooks" in out


def test_render_hook_results_mixed():
    results = [_ok("echo ok"), _fail("false")]
    out = render_hook_results(results)
    assert "✓" in out
    assert "✗" in out

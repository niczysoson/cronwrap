"""Tests for cronwrap.runlimit."""
import pytest
from unittest.mock import patch

from cronwrap.runlimit import (
    RunLimitConfig,
    run_limit_from_dict,
    count_total_runs,
    is_run_limit_exceeded,
    run_limit_status,
)


def _mock_history(entries):
    """Patch count_total_runs to return len(entries)."""
    return patch("cronwrap.runlimit.count_total_runs", return_value=len(entries))


# --- config ---

def test_config_valid():
    cfg = RunLimitConfig(max_runs=10)
    assert cfg.max_runs == 10
    assert cfg.enabled is True


def test_config_invalid():
    with pytest.raises(ValueError):
        RunLimitConfig(max_runs=0)


def test_run_limit_from_dict():
    cfg = run_limit_from_dict({"max_runs": 5, "enabled": False})
    assert cfg.max_runs == 5
    assert cfg.enabled is False


def test_run_limit_from_dict_defaults():
    cfg = run_limit_from_dict({"max_runs": 3})
    assert cfg.enabled is True


# --- is_run_limit_exceeded ---

def test_not_exceeded_below_limit():
    cfg = RunLimitConfig(max_runs=5)
    with patch("cronwrap.runlimit.count_total_runs", return_value=3):
        assert is_run_limit_exceeded(cfg, "job", "/tmp/h.json") is False


def test_exceeded_at_limit():
    cfg = RunLimitConfig(max_runs=5)
    with patch("cronwrap.runlimit.count_total_runs", return_value=5):
        assert is_run_limit_exceeded(cfg, "job", "/tmp/h.json") is True


def test_exceeded_above_limit():
    cfg = RunLimitConfig(max_runs=3)
    with patch("cronwrap.runlimit.count_total_runs", return_value=7):
        assert is_run_limit_exceeded(cfg, "job", "/tmp/h.json") is True


def test_disabled_never_exceeded():
    cfg = RunLimitConfig(max_runs=1, enabled=False)
    with patch("cronwrap.runlimit.count_total_runs", return_value=999):
        assert is_run_limit_exceeded(cfg, "job", "/tmp/h.json") is False


# --- run_limit_status ---

def test_status_not_exceeded():
    cfg = RunLimitConfig(max_runs=10)
    with patch("cronwrap.runlimit.count_total_runs", return_value=4):
        s = run_limit_status(cfg, "job", "/tmp/h.json")
    assert s["total_runs"] == 4
    assert s["remaining"] == 6
    assert s["exceeded"] is False


def test_status_exceeded():
    cfg = RunLimitConfig(max_runs=3)
    with patch("cronwrap.runlimit.count_total_runs", return_value=3):
        s = run_limit_status(cfg, "job", "/tmp/h.json")
    assert s["remaining"] == 0
    assert s["exceeded"] is True


def test_status_disabled():
    cfg = RunLimitConfig(max_runs=1, enabled=False)
    with patch("cronwrap.runlimit.count_total_runs", return_value=100):
        s = run_limit_status(cfg, "job", "/tmp/h.json")
    assert s["exceeded"] is False
    assert s["enabled"] is False

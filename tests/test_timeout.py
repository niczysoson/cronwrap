"""Tests for cronwrap.timeout and cronwrap.deadline."""
import time
import pytest

from cronwrap.timeout import TimeoutConfig, TimeoutExpired, timeout_context
from cronwrap.deadline import run_with_deadline, deadline_from_dict
from cronwrap.runner import RunResult


# ---------------------------------------------------------------------------
# TimeoutConfig
# ---------------------------------------------------------------------------

def test_timeout_config_valid():
    cfg = TimeoutConfig(seconds=5)
    assert cfg.seconds == 5
    assert cfg.kill_on_expire is True


def test_timeout_config_invalid():
    with pytest.raises(ValueError):
        TimeoutConfig(seconds=0)


# ---------------------------------------------------------------------------
# timeout_context — happy path (completes before deadline)
# ---------------------------------------------------------------------------

def test_timeout_context_no_expiry():
    cfg = TimeoutConfig(seconds=5)
    with timeout_context(cfg):
        pass  # should not raise


def test_timeout_context_none_is_noop():
    with timeout_context(None):
        time.sleep(0)  # should not raise


# ---------------------------------------------------------------------------
# run_with_deadline
# ---------------------------------------------------------------------------

def _quick_success() -> RunResult:
    return RunResult(returncode=0, stdout="ok", stderr="", duration=0.1, attempts=1)


def _quick_failure() -> RunResult:
    return RunResult(returncode=1, stdout="", stderr="err", duration=0.1, attempts=1)


def test_run_with_deadline_success():
    result = run_with_deadline(_quick_success, TimeoutConfig(seconds=5))
    assert result.returncode == 0


def test_run_with_deadline_no_timeout():
    result = run_with_deadline(_quick_failure, None)
    assert result.returncode == 1


def test_run_with_deadline_timeout_synthetic_result():
    """Simulate TimeoutExpired being raised inside fn."""
    def _slow():
        raise TimeoutExpired(2)

    # Patch timeout_context to be a noop so we can raise manually
    result = run_with_deadline(_slow, TimeoutConfig(seconds=2))
    assert result.returncode == 124
    assert "timed out" in result.stderr


# ---------------------------------------------------------------------------
# deadline_from_dict
# ---------------------------------------------------------------------------

def test_deadline_from_dict_present():
    cfg = deadline_from_dict({"timeout_seconds": 30})
    assert cfg is not None
    assert cfg.seconds == 30


def test_deadline_from_dict_absent():
    assert deadline_from_dict({}) is None


def test_deadline_from_dict_zero():
    assert deadline_from_dict({"timeout_seconds": 0}) is None


def test_deadline_from_dict_kill_flag():
    cfg = deadline_from_dict({"timeout_seconds": 10, "kill_on_expire": False})
    assert cfg.kill_on_expire is False

"""Tests for cronwrap.circuit_breaker and cronwrap.cli_circuit_breaker."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitState,
    check_circuit,
    circuit_breaker_from_dict,
)
from cronwrap.history import HistoryEntry


def _entry(job: str, exit_code: int, started_at: float | None = None) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.job_name = job
    e.exit_code = exit_code
    e.started_at = started_at or time.time()
    e.succeeded.return_value = exit_code == 0
    return e


def _history(entries):
    h = MagicMock()
    h.for_job.return_value = entries
    return h


def test_config_valid():
    cfg = CircuitBreakerConfig(failure_threshold=2, recovery_seconds=60)
    assert cfg.failure_threshold == 2


def test_config_invalid_threshold():
    with pytest.raises(ValueError):
        CircuitBreakerConfig(failure_threshold=0)


def test_config_invalid_recovery():
    with pytest.raises(ValueError):
        CircuitBreakerConfig(recovery_seconds=-1)


def test_circuit_breaker_from_dict():
    cfg = circuit_breaker_from_dict({"failure_threshold": "4", "recovery_seconds": "120"})
    assert cfg.failure_threshold == 4
    assert cfg.recovery_seconds == 120


def test_circuit_closed_on_no_failures():
    cfg = CircuitBreakerConfig(failure_threshold=3)
    h = _history([_entry("j", 0), _entry("j", 0)])
    state = check_circuit("j", cfg, h)
    assert not state.open
    assert state.consecutive_failures == 0


def test_circuit_closed_below_threshold():
    cfg = CircuitBreakerConfig(failure_threshold=3)
    h = _history([_entry("j", 0), _entry("j", 1), _entry("j", 1)])
    state = check_circuit("j", cfg, h)
    assert not state.open
    assert state.consecutive_failures == 2


def test_circuit_opens_at_threshold():
    cfg = CircuitBreakerConfig(failure_threshold=3, recovery_seconds=300)
    entries = [_entry("j", 1) for _ in range(3)]
    h = _history(entries)
    state = check_circuit("j", cfg, h)
    assert state.open
    assert state.consecutive_failures == 3
    assert state.opened_at is not None


def test_circuit_disabled_always_closed():
    cfg = CircuitBreakerConfig(failure_threshold=1, enabled=False)
    h = _history([_entry("j", 1), _entry("j", 1)])
    state = check_circuit("j", cfg, h)
    assert not state.open


def test_half_open_after_recovery():
    state = CircuitState(open=True, consecutive_failures=3,
                         opened_at=time.time() - 400, recovery_seconds=300)
    assert state.half_open
    assert state.seconds_until_recovery == 0.0


def test_not_half_open_during_recovery():
    state = CircuitState(open=True, consecutive_failures=3,
                         opened_at=time.time(), recovery_seconds=300)
    assert not state.half_open
    assert state.seconds_until_recovery > 0

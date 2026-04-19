"""Tests for cronwrap.cli_circuit_breaker."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.circuit_breaker import CircuitBreakerConfig, CircuitState
from cronwrap.cli_circuit_breaker import (
    _fmt_seconds,
    check_and_exit_if_open,
    render_circuit_status,
)


def _state(open_: bool, failures: int, opened_at=None, recovery=300):
    return CircuitState(
        open=open_,
        consecutive_failures=failures,
        opened_at=opened_at,
        recovery_seconds=recovery,
    )


def test_fmt_seconds_under_minute():
    assert _fmt_seconds(45) == "45s"


def test_fmt_seconds_over_minute():
    assert _fmt_seconds(125) == "2m05s"


def test_render_closed():
    out = render_circuit_status("backup", _state(False, 1))
    assert "CLOSED" in out
    assert "backup" in out


def test_render_open():
    out = render_circuit_status("backup", _state(True, 4, opened_at=time.time()))
    assert "OPEN" in out
    assert "Recovery in" in out


def test_render_half_open():
    out = render_circuit_status("backup", _state(True, 4, opened_at=time.time() - 400))
    assert "HALF-OPEN" in out


def test_check_closed_does_not_exit():
    cfg = CircuitBreakerConfig(failure_threshold=3)
    h = MagicMock()
    h.for_job.return_value = []
    state = check_and_exit_if_open("job", cfg, h)
    assert not state.open


def test_check_open_exits_with_2():
    cfg = CircuitBreakerConfig(failure_threshold=2, recovery_seconds=9999)
    from cronwrap.history import HistoryEntry
    e = MagicMock(spec=HistoryEntry)
    e.succeeded.return_value = False
    e.started_at = time.time()
    h = MagicMock()
    h.for_job.return_value = [e, e]
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_open("job", cfg, h)
    assert exc.value.code == 2


def test_check_half_open_does_not_exit():
    cfg = CircuitBreakerConfig(failure_threshold=2, recovery_seconds=1)
    from cronwrap.history import HistoryEntry
    e = MagicMock(spec=HistoryEntry)
    e.succeeded.return_value = False
    e.started_at = time.time() - 10   # recovery elapsed
    h = MagicMock()
    h.for_job.return_value = [e, e]
    state = check_and_exit_if_open("job", cfg, h)
    assert state.half_open

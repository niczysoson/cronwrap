"""CLI rendering for circuit breaker status."""
from __future__ import annotations

import sys

from cronwrap.circuit_breaker import CircuitBreakerConfig, CircuitState, check_circuit
from cronwrap.history import JobHistory


def _fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    m = int(s) // 60
    sec = int(s) % 60
    return f"{m}m{sec:02d}s"


def render_circuit_status(job_name: str, state: CircuitState) -> str:
    lines = [f"Circuit breaker — {job_name}"]
    if not state.open:
        lines.append(f"  Status : CLOSED (consecutive failures: {state.consecutive_failures})")
    elif state.half_open:
        lines.append(f"  Status : HALF-OPEN (ready for retry)")
        lines.append(f"  Consecutive failures: {state.consecutive_failures}")
    else:
        lines.append(f"  Status : OPEN")
        lines.append(f"  Consecutive failures: {state.consecutive_failures}")
        lines.append(f"  Recovery in        : {_fmt_seconds(state.seconds_until_recovery)}")
    return "\n".join(lines)


def check_and_exit_if_open(
    job_name: str,
    cfg: CircuitBreakerConfig,
    history: JobHistory,
) -> CircuitState:
    """Print status; exit with code 2 if circuit is open and not half-open."""
    state = check_circuit(job_name, cfg, history)
    print(render_circuit_status(job_name, state))
    if state.open and not state.half_open:
        print("[circuit-breaker] Job skipped — circuit is OPEN.", file=sys.stderr)
        sys.exit(2)
    return state

"""Circuit breaker: pause a job after too many consecutive failures."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import HistoryEntry, JobHistory


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3        # consecutive failures to open circuit
    recovery_seconds: int = 300       # seconds to wait before half-open
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_seconds < 0:
            raise ValueError("recovery_seconds must be >= 0")


def circuit_breaker_from_dict(d: dict) -> CircuitBreakerConfig:
    return CircuitBreakerConfig(
        failure_threshold=int(d.get("failure_threshold", 3)),
        recovery_seconds=int(d.get("recovery_seconds", 300)),
        enabled=bool(d.get("enabled", True)),
    )


@dataclass
class CircuitState:
    open: bool
    consecutive_failures: int
    opened_at: Optional[float]   # epoch seconds
    recovery_seconds: int

    @property
    def seconds_until_recovery(self) -> float:
        if not self.open or self.opened_at is None:
            return 0.0
        elapsed = time.time() - self.opened_at
        remaining = self.recovery_seconds - elapsed
        return max(0.0, remaining)

    @property
    def half_open(self) -> bool:
        return self.open and self.seconds_until_recovery == 0.0


def check_circuit(
    job_name: str,
    cfg: CircuitBreakerConfig,
    history: JobHistory,
) -> CircuitState:
    """Inspect recent history and return the current circuit state."""
    if not cfg.enabled:
        return CircuitState(open=False, consecutive_failures=0, opened_at=None,
                            recovery_seconds=cfg.recovery_seconds)

    entries: List[HistoryEntry] = history.for_job(job_name)
    # Walk backwards counting consecutive failures
    consecutive = 0
    opened_at: Optional[float] = None
    for entry in reversed(entries):
        if entry.succeeded():
            break
        consecutive += 1
        opened_at = entry.started_at

    is_open = consecutive >= cfg.failure_threshold
    return CircuitState(
        open=is_open,
        consecutive_failures=consecutive,
        opened_at=opened_at if is_open else None,
        recovery_seconds=cfg.recovery_seconds,
    )

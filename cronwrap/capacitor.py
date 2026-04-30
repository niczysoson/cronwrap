"""capacitor.py – burst-capacity guard for cron jobs.

Prevents a job from running if it has exceeded a maximum number of
concurrent *or* queued executions within a rolling time window.
This is distinct from rate-limiting (which counts completions) and
concurrency (which counts active slots): the capacitor counts *starts*
in a window and blocks new starts once the cap is reached.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwrap.history import HistoryStore, HistoryEntry


@dataclasses.dataclass
class CapacitorConfig:
    max_starts: int = 5
    window_seconds: int = 3600
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
        if self.max_starts < 1:
            raise ValueError("max_starts must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


def capacitor_from_dict(data: dict) -> CapacitorConfig:
    return CapacitorConfig(
        max_starts=int(data.get("max_starts", 5)),
        window_seconds=int(data.get("window_seconds", 3600)),
        enabled=bool(data.get("enabled", True)),
    )


def count_starts_in_window(
    job_name: str,
    store: HistoryStore,
    window_seconds: int,
) -> int:
    """Return the number of job starts recorded within the rolling window."""
    cutoff: datetime = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    entries: List[HistoryEntry] = store.for_job(job_name)
    return sum(1 for e in entries if e.started_at >= cutoff)


@dataclasses.dataclass
class CapacitorResult:
    allowed: bool
    starts_in_window: int
    max_starts: int
    window_seconds: int

    def summary(self) -> str:
        status = "allowed" if self.allowed else "blocked"
        return (
            f"Capacitor {status}: {self.starts_in_window}/{self.max_starts} "
            f"starts in last {self.window_seconds}s"
        )


def check_capacity(
    job_name: str,
    cfg: CapacitorConfig,
    store: HistoryStore,
) -> CapacitorResult:
    """Check whether the job is within its burst capacity."""
    if not cfg.enabled:
        return CapacitorResult(
            allowed=True,
            starts_in_window=0,
            max_starts=cfg.max_starts,
            window_seconds=cfg.window_seconds,
        )
    starts = count_starts_in_window(job_name, store, cfg.window_seconds)
    return CapacitorResult(
        allowed=starts < cfg.max_starts,
        starts_in_window=starts,
        max_starts=cfg.max_starts,
        window_seconds=cfg.window_seconds,
    )

"""Rate limiting: cap how many times a job can succeed within a time window."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import HistoryStore, HistoryEntry


@dataclass
class RateLimitConfig:
    max_runs: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


def rate_limit_from_dict(d: dict) -> Optional[RateLimitConfig]:
    if not d:
        return None
    return RateLimitConfig(
        max_runs=int(d["max_runs"]),
        window_seconds=int(d["window_seconds"]),
    )


def count_recent_runs(entries: List[HistoryEntry], window_seconds: int) -> int:
    """Count successful runs within the trailing window."""
    cutoff = time.time() - window_seconds
    return sum(
        1 for e in entries if e.succeeded and e.started_at >= cutoff
    )


def is_rate_limited(
    job_name: str,
    config: RateLimitConfig,
    store: HistoryStore,
) -> bool:
    entries = store.get(job_name)
    recent = count_recent_runs(entries, config.window_seconds)
    return recent >= config.max_runs


def rate_limit_status(job_name: str, config: RateLimitConfig, store: HistoryStore) -> dict:
    entries = store.get(job_name)
    recent = count_recent_runs(entries, config.window_seconds)
    return {
        "job": job_name,
        "max_runs": config.max_runs,
        "window_seconds": config.window_seconds,
        "recent_runs": recent,
        "limited": recent >= config.max_runs,
    }

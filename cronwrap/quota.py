"""Run quota enforcement – cap how many times a job may run in a time window."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from cronwrap.history import HistoryStore


@dataclass
class QuotaConfig:
    max_runs: int
    window_seconds: int
    job_name: str = ""

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


def quota_from_dict(d: dict) -> QuotaConfig:
    return QuotaConfig(
        max_runs=int(d["max_runs"]),
        window_seconds=int(d["window_seconds"]),
        job_name=d.get("job_name", ""),
    )


def count_runs_in_window(entries: List, window_seconds: int) -> int:
    """Return how many history entries fall within the rolling window."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    return sum(1 for e in entries if e.started_at >= cutoff)


def is_quota_exceeded(cfg: QuotaConfig, store: HistoryStore) -> bool:
    entries = store.get(cfg.job_name) if cfg.job_name else store.all()
    runs = count_runs_in_window(entries, cfg.window_seconds)
    return runs >= cfg.max_runs


def quota_status(cfg: QuotaConfig, store: HistoryStore) -> dict:
    entries = store.get(cfg.job_name) if cfg.job_name else store.all()
    runs = count_runs_in_window(entries, cfg.window_seconds)
    return {
        "job_name": cfg.job_name,
        "max_runs": cfg.max_runs,
        "window_seconds": cfg.window_seconds,
        "runs_in_window": runs,
        "exceeded": runs >= cfg.max_runs,
        "remaining": max(0, cfg.max_runs - runs),
    }

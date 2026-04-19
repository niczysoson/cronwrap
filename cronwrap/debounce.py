"""Debounce: skip a job run if it ran too recently (within a cooldown window)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import JobHistory


@dataclass
class DebounceConfig:
    cooldown_seconds: int
    job_name: str

    def __post_init__(self) -> None:
        if self.cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be positive")
        if not self.job_name:
            raise ValueError("job_name must not be empty")


def debounce_from_dict(d: dict) -> DebounceConfig:
    return DebounceConfig(
        cooldown_seconds=int(d["cooldown_seconds"]),
        job_name=str(d["job_name"]),
    )


def last_run_time(cfg: DebounceConfig, history: JobHistory) -> Optional[datetime]:
    entries = history.get(cfg.job_name)
    if not entries:
        return None
    return max(e.started_at for e in entries)


def is_debounced(cfg: DebounceConfig, history: JobHistory) -> bool:
    """Return True if the job ran within the cooldown window."""
    last = last_run_time(cfg, history)
    if last is None:
        return False
    now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()
    return elapsed < cfg.cooldown_seconds


def elapsed_seconds(cfg: DebounceConfig, history: JobHistory) -> Optional[float]:
    last = last_run_time(cfg, history)
    if last is None:
        return None
    return (datetime.now(timezone.utc) - last).total_seconds()

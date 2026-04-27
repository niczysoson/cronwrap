"""cooldown_window.py – skip a job if it ran successfully within a time window.

Differs from `cooldown.py` (which gates on *failures*): this module gates on
*successes*, letting operators prevent a job from running more frequently than
a desired minimum interval regardless of outcome.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import JobHistory


@dataclasses.dataclass
class CooldownWindowConfig:
    """Configuration for success-based cooldown windows."""

    min_interval_seconds: int
    job_name: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.min_interval_seconds <= 0:
            raise ValueError("min_interval_seconds must be a positive integer")
        if not self.job_name or not self.job_name.strip():
            raise ValueError("job_name must not be empty")


def cooldown_window_from_dict(data: dict) -> CooldownWindowConfig:
    """Build a CooldownWindowConfig from a plain dictionary (e.g. parsed YAML)."""
    return CooldownWindowConfig(
        min_interval_seconds=int(data["min_interval_seconds"]),
        job_name=str(data["job_name"]),
        enabled=bool(data.get("enabled", True)),
    )


def last_success_time(cfg: CooldownWindowConfig, history: JobHistory) -> Optional[datetime]:
    """Return the timestamp of the most recent successful run, or *None*."""
    entries = history.for_job(cfg.job_name)
    successes = [e for e in entries if e.succeeded]
    if not successes:
        return None
    return max(e.finished_at for e in successes)


def is_in_cooldown_window(
    cfg: CooldownWindowConfig,
    history: JobHistory,
    now: Optional[datetime] = None,
) -> bool:
    """Return *True* when the job should be skipped due to a recent success."""
    if not cfg.enabled:
        return False
    last = last_success_time(cfg, history)
    if last is None:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()
    return elapsed < cfg.min_interval_seconds


def seconds_remaining(
    cfg: CooldownWindowConfig,
    history: JobHistory,
    now: Optional[datetime] = None,
) -> float:
    """Return how many seconds remain in the cooldown window (0 if not cooling)."""
    if not cfg.enabled:
        return 0.0
    last = last_success_time(cfg, history)
    if last is None:
        return 0.0
    if now is None:
        now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()
    remaining = cfg.min_interval_seconds - elapsed
    return max(0.0, remaining)

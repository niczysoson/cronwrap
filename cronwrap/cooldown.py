"""Cooldown: prevent a job from running too soon after a failure."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import JobHistory


@dataclass
class CooldownConfig:
    """Configuration for post-failure cooldown."""
    seconds: int = 300
    job_name: str = ""

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError("cooldown seconds must be >= 0")


def cooldown_from_dict(d: dict) -> CooldownConfig:
    return CooldownConfig(
        seconds=int(d.get("seconds", 300)),
        job_name=str(d.get("job_name", "")),
    )


def last_failure_time(job_name: str, history: JobHistory) -> Optional[datetime]:
    """Return the timestamp of the most recent failure, or None."""
    entries = history.get(job_name)
    failures = [e for e in entries if not e.succeeded]
    if not failures:
        return None
    return max(e.finished_at for e in failures)


def is_cooling_down(config: CooldownConfig, history: JobHistory) -> bool:
    """Return True if the job is still within its post-failure cooldown window."""
    if config.seconds == 0:
        return False
    last = last_failure_time(config.job_name, history)
    if last is None:
        return False
    now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()
    return elapsed < config.seconds


def seconds_remaining(config: CooldownConfig, history: JobHistory) -> float:
    """Return how many seconds remain in the cooldown window (0 if not cooling)."""
    if not is_cooling_down(config, history):
        return 0.0
    last = last_failure_time(config.job_name, history)
    now = datetime.now(timezone.utc)
    elapsed = (now - last).total_seconds()
    return max(0.0, config.seconds - elapsed)

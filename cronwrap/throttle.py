"""Rate limiting / throttle logic for cron jobs.

Prevents a job from running more frequently than a minimum interval,
regardless of the cron schedule.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json

from cronwrap.history import JobHistory


@dataclass
class ThrottleConfig:
    min_interval_seconds: int  # minimum seconds between successful runs
    state_dir: Path = field(default_factory=lambda: Path(".cronwrap"))

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        self.state_dir = Path(self.state_dir)


def _stamp_path(state_dir: Path, job_name: str) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return state_dir / f"{safe}.throttle.json"


def last_success_time(job_name: str, history: JobHistory) -> Optional[float]:
    """Return epoch of most recent successful run, or None."""
    entries = history.get(job_name)
    successes = [e for e in entries if e.succeeded]
    if not successes:
        return None
    return max(e.started_at for e in successes)


def is_throttled(job_name: str, cfg: ThrottleConfig, history: JobHistory) -> bool:
    """Return True if the job ran successfully too recently."""
    last = last_success_time(job_name, history)
    if last is None:
        return False
    elapsed = time.time() - last
    return elapsed < cfg.min_interval_seconds


def throttle_from_dict(d: dict) -> Optional[ThrottleConfig]:
    if not d:
        return None
    return ThrottleConfig(
        min_interval_seconds=int(d["min_interval_seconds"]),
        state_dir=Path(d.get("state_dir", ".cronwrap")),
    )

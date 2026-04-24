"""Stagger: spread job starts across a time window to avoid thundering-herd."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StaggerConfig:
    """Configuration for staggered job start times."""

    enabled: bool = True
    # Total window in seconds across which jobs are spread.
    window_seconds: int = 60
    # Seed string used to deterministically assign a slot (e.g. job name).
    seed: str = ""
    # If True, actually sleep; if False, only return the delay.
    sleep_enabled: bool = True

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if not isinstance(self.seed, str):
            raise TypeError("seed must be a string")

    def delay(self) -> float:
        """Return deterministic delay in [0, window_seconds) seconds."""
        if not self.enabled or self.window_seconds == 0:
            return 0.0
        digest = hashlib.md5(self.seed.encode()).hexdigest()  # noqa: S324
        slot = int(digest[:8], 16)
        return (slot % (self.window_seconds * 1000)) / 1000.0

    def sleep(self) -> float:
        """Sleep for the computed delay and return it."""
        secs = self.delay()
        if self.sleep_enabled and secs > 0:
            time.sleep(secs)
        return secs

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "window_seconds": self.window_seconds,
            "seed": self.seed,
            "sleep_enabled": self.sleep_enabled,
        }


def stagger_from_dict(data: dict) -> StaggerConfig:
    """Build a StaggerConfig from a plain dictionary."""
    return StaggerConfig(
        enabled=bool(data.get("enabled", True)),
        window_seconds=int(data.get("window_seconds", 60)),
        seed=str(data.get("seed", "")),
        sleep_enabled=bool(data.get("sleep_enabled", True)),
    )

"""Jitter config: randomise job start time to avoid thundering herd."""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterConfig:
    enabled: bool = True
    max_seconds: int = 30
    seed: Optional[int] = None  # for testing

    def __post_init__(self) -> None:
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")

    def delay(self) -> float:
        """Return a random delay in [0, max_seconds]."""
        if not self.enabled or self.max_seconds == 0:
            return 0.0
        rng = random.Random(self.seed)
        return rng.uniform(0, self.max_seconds)

    def sleep(self) -> float:
        """Sleep for the jitter delay and return the actual seconds slept."""
        secs = self.delay()
        if secs > 0:
            time.sleep(secs)
        return secs

    def to_dict(self) -> dict:
        return {"enabled": self.enabled, "max_seconds": self.max_seconds}


def jitter_from_dict(data: dict) -> JitterConfig:
    return JitterConfig(
        enabled=bool(data.get("enabled", True)),
        max_seconds=int(data.get("max_seconds", 30)),
    )


def render_jitter(cfg: JitterConfig) -> str:
    if not cfg.enabled:
        return "Jitter: disabled"
    return f"Jitter: enabled  max={cfg.max_seconds}s"

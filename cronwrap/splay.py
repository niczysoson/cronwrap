"""Splay: randomise job start time within a window to avoid thundering herd."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SplayConfig:
    """Configuration for splay (start-time randomisation)."""
    max_seconds: int = 0
    enabled: bool = True
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")
        self._rng = random.Random(self.seed)

    def delay(self) -> float:
        """Return a random delay in [0, max_seconds]."""
        if not self.enabled or self.max_seconds == 0:
            return 0.0
        return self._rng.uniform(0, self.max_seconds)

    def sleep(self) -> float:
        """Sleep for the computed delay; return actual seconds slept."""
        secs = self.delay()
        if secs > 0:
            time.sleep(secs)
        return secs

    def to_dict(self) -> dict:
        return {
            "max_seconds": self.max_seconds,
            "enabled": self.enabled,
            "seed": self.seed,
        }


def splay_from_dict(data: dict) -> SplayConfig:
    """Construct a SplayConfig from a plain dict (e.g. from YAML/JSON config)."""
    return SplayConfig(
        max_seconds=int(data.get("max_seconds", 0)),
        enabled=bool(data.get("enabled", True)),
        seed=data.get("seed"),
    )


def render_splay_status(cfg: SplayConfig) -> str:
    """Return a human-readable summary of the splay configuration."""
    if not cfg.enabled or cfg.max_seconds == 0:
        return "splay: disabled"
    return f"splay: up to {cfg.max_seconds}s random delay before start"

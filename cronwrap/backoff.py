"""Backoff strategies for retry delays."""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Literal

Strategy = Literal["fixed", "linear", "exponential", "jitter"]


@dataclass
class BackoffConfig:
    strategy: Strategy = "fixed"
    base_delay: float = 1.0
    max_delay: float = 300.0
    multiplier: float = 2.0
    jitter: bool = False

    def __post_init__(self) -> None:
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")
        if self.strategy not in ("fixed", "linear", "exponential", "jitter"):
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def delay_for(self, attempt: int) -> float:
        """Return delay in seconds for the given attempt number (1-based)."""
        if self.strategy == "fixed":
            delay = self.base_delay
        elif self.strategy == "linear":
            delay = self.base_delay * attempt
        elif self.strategy == "exponential":
            delay = self.base_delay * (self.multiplier ** (attempt - 1))
        elif self.strategy == "jitter":
            upper = min(self.base_delay * (self.multiplier ** (attempt - 1)), self.max_delay)
            delay = random.uniform(0, upper)
        else:
            delay = self.base_delay

        if self.strategy != "jitter":
            delay = min(delay, self.max_delay)
            if self.jitter:
                delay = random.uniform(0, delay)
        return round(delay, 3)


def backoff_from_dict(d: dict) -> BackoffConfig:
    return BackoffConfig(
        strategy=d.get("strategy", "fixed"),
        base_delay=float(d.get("base_delay", 1.0)),
        max_delay=float(d.get("max_delay", 300.0)),
        multiplier=float(d.get("multiplier", 2.0)),
        jitter=bool(d.get("jitter", False)),
    )


def render_backoff(cfg: BackoffConfig) -> str:
    lines = [
        f"  Strategy : {cfg.strategy}",
        f"  Base delay: {cfg.base_delay}s",
        f"  Max delay : {cfg.max_delay}s",
        f"  Multiplier: {cfg.multiplier}",
        f"  Jitter    : {'yes' if cfg.jitter else 'no'}",
    ]
    return "\n".join(lines)

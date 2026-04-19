"""Unified pre-run sleep combining jitter and a fixed startup delay."""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
from cronwrap.jitter import JitterConfig, jitter_from_dict


@dataclass
class SleepConfig:
    fixed_seconds: float = 0.0
    jitter: Optional[JitterConfig] = None

    def __post_init__(self) -> None:
        if self.fixed_seconds < 0:
            raise ValueError("fixed_seconds must be >= 0")

    def total_delay(self) -> float:
        jitter_secs = self.jitter.delay() if self.jitter else 0.0
        return self.fixed_seconds + jitter_secs

    def apply(self) -> float:
        """Sleep for the combined delay; return seconds slept."""
        secs = self.total_delay()
        if secs > 0:
            time.sleep(secs)
        return secs

    def to_dict(self) -> dict:
        d: dict = {"fixed_seconds": self.fixed_seconds}
        if self.jitter:
            d["jitter"] = self.jitter.to_dict()
        return d


def sleep_from_dict(data: dict) -> SleepConfig:
    jitter = jitter_from_dict(data["jitter"]) if "jitter" in data else None
    return SleepConfig(
        fixed_seconds=float(data.get("fixed_seconds", 0.0)),
        jitter=jitter,
    )

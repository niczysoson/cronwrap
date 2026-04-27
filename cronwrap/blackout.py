"""Blackout window support — prevent jobs from running during defined time ranges."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional


@dataclass
class BlackoutConfig:
    """Configuration for blackout windows."""

    windows: List[str] = field(default_factory=list)  # e.g. ["22:00-06:00", "12:00-13:00"]
    enabled: bool = True

    _TIME_RE = re.compile(r'^(\d{2}:\d{2})-(\d{2}:\d{2})$')

    def __post_init__(self) -> None:
        if not isinstance(self.windows, list):
            raise ValueError("windows must be a list")
        for w in self.windows:
            if not self._TIME_RE.match(w):
                raise ValueError(f"Invalid blackout window format: {w!r} (expected HH:MM-HH:MM)")

    @staticmethod
    def _parse_time(s: str) -> time:
        h, m = s.split(":")
        return time(int(h), int(m))

    def is_blacked_out(self, now: Optional[datetime] = None) -> bool:
        """Return True if *now* falls within any blackout window."""
        if not self.enabled or not self.windows:
            return False
        if now is None:
            now = datetime.utcnow()
        current = now.time().replace(second=0, microsecond=0)
        for window in self.windows:
            m = self._TIME_RE.match(window)
            start = self._parse_time(m.group(1))
            end = self._parse_time(m.group(2))
            if start <= end:
                if start <= current < end:
                    return True
            else:  # wraps midnight
                if current >= start or current < end:
                    return True
        return False

    def to_dict(self) -> dict:
        return {"windows": self.windows, "enabled": self.enabled}


def blackout_from_dict(d: dict) -> BlackoutConfig:
    return BlackoutConfig(
        windows=d.get("windows", []),
        enabled=bool(d.get("enabled", True)),
    )

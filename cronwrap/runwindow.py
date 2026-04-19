"""Run window: restrict job execution to allowed time windows."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional


@dataclass
class RunWindowConfig:
    """Configuration for allowed execution windows."""
    windows: List[tuple]  # list of (start_time_str, end_time_str) e.g. ("08:00", "18:00")
    enabled: bool = True
    timezone: str = "UTC"  # informational only; caller handles tz

    def __post_init__(self):
        if not self.windows:
            raise ValueError("At least one time window must be specified")
        parsed = []
        for start_str, end_str in self.windows:
            start = _parse_time(start_str)
            end = _parse_time(end_str)
            if start >= end:
                raise ValueError(
                    f"Window start {start_str} must be before end {end_str}"
                )
            parsed.append((start, end))
        self._parsed: List[tuple] = parsed

    def is_allowed(self, now: Optional[datetime] = None) -> bool:
        """Return True if *now* falls within any configured window."""
        if not self.enabled:
            return True
        t = (now or datetime.utcnow()).time().replace(second=0, microsecond=0)
        for start, end in self._parsed:
            if start <= t <= end:
                return True
        return False

    def next_window_start(self, now: Optional[datetime] = None) -> Optional[time]:
        """Return the start of the next window after *now*, or None."""
        t = (now or datetime.utcnow()).time().replace(second=0, microsecond=0)
        future = [start for start, _ in self._parsed if start > t]
        return min(future) if future else None

    def to_dict(self) -> dict:
        return {
            "windows": [
                {"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M")}
                for s, e in self._parsed
            ],
            "enabled": self.enabled,
            "timezone": self.timezone,
        }


def _parse_time(value: str) -> time:
    try:
        h, m = value.strip().split(":")
        return time(int(h), int(m))
    except Exception:
        raise ValueError(f"Invalid time format '{value}', expected HH:MM")


def runwindow_from_dict(data: dict) -> RunWindowConfig:
    raw = data.get("windows", [])
    windows = [(w["start"], w["end"]) for w in raw]
    return RunWindowConfig(
        windows=windows,
        enabled=data.get("enabled", True),
        timezone=data.get("timezone", "UTC"),
    )

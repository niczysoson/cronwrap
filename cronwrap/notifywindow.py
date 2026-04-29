"""Notification window: suppress alerts outside allowed time ranges."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional

_TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')


@dataclass
class NotifyWindowConfig:
    """Config for suppressing notifications outside a time window."""
    enabled: bool = True
    windows: List[str] = field(default_factory=list)  # e.g. ["08:00-18:00"]
    timezone: str = "UTC"  # informational only; caller handles tz conversion

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if not isinstance(self.windows, list):
            raise ValueError("windows must be a list")
        for w in self.windows:
            _parse_window(w)  # validate each entry


@dataclass
class NotifyWindowResult:
    allowed: bool
    reason: str

    def summary(self) -> str:
        status = "allowed" if self.allowed else "suppressed"
        return f"Notification {status}: {self.reason}"


def _parse_time(s: str) -> time:
    m = _TIME_RE.match(s.strip())
    if not m:
        raise ValueError(f"Invalid time format '{s}'; expected HH:MM")
    h, mi = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        raise ValueError(f"Time out of range: {s}")
    return time(h, mi)


def _parse_window(window: str):
    parts = window.split("-")
    if len(parts) != 2:
        raise ValueError(f"Window must be 'HH:MM-HH:MM', got '{window}'")
    start = _parse_time(parts[0])
    end = _parse_time(parts[1])
    if start >= end:
        raise ValueError(f"Window start must be before end: '{window}'")
    return start, end


def is_notify_allowed(
    cfg: NotifyWindowConfig,
    now: Optional[datetime] = None,
) -> NotifyWindowResult:
    """Return whether a notification should be sent at *now*."""
    if not cfg.enabled:
        return NotifyWindowResult(allowed=True, reason="notify window disabled")
    if not cfg.windows:
        return NotifyWindowResult(allowed=True, reason="no windows configured")

    if now is None:
        now = datetime.utcnow()
    current = now.time().replace(second=0, microsecond=0)

    for w in cfg.windows:
        start, end = _parse_window(w)
        if start <= current <= end:
            return NotifyWindowResult(
                allowed=True,
                reason=f"within window {w}",
            )

    return NotifyWindowResult(
        allowed=False,
        reason=f"outside all windows at {current.strftime('%H:%M')}",
    )


def notify_window_from_dict(d: dict) -> NotifyWindowConfig:
    return NotifyWindowConfig(
        enabled=d.get("enabled", True),
        windows=d.get("windows", []),
        timezone=d.get("timezone", "UTC"),
    )

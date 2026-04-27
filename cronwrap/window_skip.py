"""window_skip.py — Skip job execution outside of allowed date ranges.

Allows jobs to be restricted to a calendar window (e.g. only run between
2024-01-01 and 2024-03-31) with optional soft-skip (warn) vs hard-skip (exit).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WindowSkipConfig:
    enabled: bool = True
    start_date: Optional[datetime.date] = None  # inclusive
    end_date: Optional[datetime.date] = None    # inclusive
    soft: bool = False  # if True, warn only; if False, skip/exit

    def __post_init__(self) -> None:
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError(
                    f"start_date {self.start_date} must be <= end_date {self.end_date}"
                )

    def is_in_window(self, when: Optional[datetime.date] = None) -> bool:
        """Return True if *when* (default: today) falls within the configured window."""
        if not self.enabled:
            return True
        today = when or datetime.date.today()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "soft": self.soft,
        }


def window_skip_from_dict(data: dict) -> WindowSkipConfig:
    def _parse(val: Optional[str]) -> Optional[datetime.date]:
        return datetime.date.fromisoformat(val) if val else None

    return WindowSkipConfig(
        enabled=bool(data.get("enabled", True)),
        start_date=_parse(data.get("start_date")),
        end_date=_parse(data.get("end_date")),
        soft=bool(data.get("soft", False)),
    )


def should_skip(cfg: WindowSkipConfig, when: Optional[datetime.date] = None) -> bool:
    """Return True when the job should be skipped (outside window and not soft)."""
    if not cfg.enabled:
        return False
    return not cfg.is_in_window(when)


def skip_reason(cfg: WindowSkipConfig, when: Optional[datetime.date] = None) -> str:
    today = when or datetime.date.today()
    parts = []
    if cfg.start_date and today < cfg.start_date:
        parts.append(f"before start_date {cfg.start_date}")
    if cfg.end_date and today > cfg.end_date:
        parts.append(f"after end_date {cfg.end_date}")
    return "; ".join(parts) if parts else "within window"

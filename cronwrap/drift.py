"""Drift detection: warn when a job runs significantly later than scheduled."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Optional


@dataclasses.dataclass
class DriftConfig:
    """Configuration for schedule drift detection."""
    max_drift_seconds: int = 300          # warn if job starts more than this late
    warn_only: bool = True                # if False, exit non-zero when drift exceeded
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_drift_seconds <= 0:
            raise ValueError("max_drift_seconds must be positive")


@dataclasses.dataclass
class DriftResult:
    scheduled_at: datetime
    actual_at: datetime
    max_drift_seconds: int

    @property
    def drift_seconds(self) -> float:
        delta = self.actual_at - self.scheduled_at
        return delta.total_seconds()

    @property
    def exceeded(self) -> bool:
        return self.drift_seconds > self.max_drift_seconds

    def summary(self) -> str:
        drift = self.drift_seconds
        status = "EXCEEDED" if self.exceeded else "ok"
        return (
            f"drift={drift:.1f}s  max={self.max_drift_seconds}s  [{status}]"
        )


def drift_from_dict(d: dict) -> DriftConfig:
    return DriftConfig(
        max_drift_seconds=int(d.get("max_drift_seconds", 300)),
        warn_only=bool(d.get("warn_only", True)),
        enabled=bool(d.get("enabled", True)),
    )


def measure_drift(
    config: DriftConfig,
    scheduled_at: datetime,
    actual_at: Optional[datetime] = None,
) -> DriftResult:
    """Return a DriftResult comparing scheduled vs actual start time."""
    if actual_at is None:
        actual_at = datetime.now(timezone.utc)
    return DriftResult(
        scheduled_at=scheduled_at,
        actual_at=actual_at,
        max_drift_seconds=config.max_drift_seconds,
    )

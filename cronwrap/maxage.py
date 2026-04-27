"""Maximum age enforcement for cron job outputs.

Allows jobs to be skipped or flagged when their last successful run
exceeds a configured maximum age threshold.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Optional


@dataclasses.dataclass
class MaxAgeConfig:
    """Configuration for maximum age enforcement."""

    max_seconds: float
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_seconds <= 0:
            raise ValueError("max_seconds must be positive")


def maxage_from_dict(d: dict) -> MaxAgeConfig:
    """Build a MaxAgeConfig from a plain dictionary."""
    return MaxAgeConfig(
        max_seconds=float(d["max_seconds"]),
        enabled=bool(d.get("enabled", True)),
    )


@dataclasses.dataclass
class MaxAgeResult:
    """Result of a maximum-age check."""

    last_success: Optional[datetime]
    age_seconds: Optional[float]
    exceeded: bool
    max_seconds: float

    def summary(self) -> str:
        if not self.exceeded:
            if self.age_seconds is None:
                return "no previous success recorded"
            return f"last success {self.age_seconds:.1f}s ago (limit {self.max_seconds:.1f}s)"
        if self.age_seconds is None:
            return f"no previous success; limit {self.max_seconds:.1f}s exceeded"
        return (
            f"last success {self.age_seconds:.1f}s ago exceeds limit "
            f"{self.max_seconds:.1f}s"
        )


def check_max_age(
    cfg: MaxAgeConfig,
    last_success: Optional[datetime],
    now: Optional[datetime] = None,
) -> MaxAgeResult:
    """Check whether *last_success* is within the allowed maximum age.

    Parameters
    ----------
    cfg:
        The MaxAgeConfig to enforce.
    last_success:
        The timestamp of the most recent successful run, or ``None``.
    now:
        Reference time (defaults to ``datetime.now(timezone.utc)``).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if not cfg.enabled:
        return MaxAgeResult(
            last_success=last_success,
            age_seconds=None,
            exceeded=False,
            max_seconds=cfg.max_seconds,
        )

    if last_success is None:
        return MaxAgeResult(
            last_success=None,
            age_seconds=None,
            exceeded=True,
            max_seconds=cfg.max_seconds,
        )

    age = (now - last_success).total_seconds()
    return MaxAgeResult(
        last_success=last_success,
        age_seconds=age,
        exceeded=age > cfg.max_seconds,
        max_seconds=cfg.max_seconds,
    )

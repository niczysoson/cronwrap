"""Grace period support: suppress alerts/failures for a job during an initial warm-up window."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import JobHistory


@dataclasses.dataclass
class GraceConfig:
    """Configuration for a grace period applied to a job."""

    enabled: bool = True
    # Number of seconds after the very first recorded run during which failures are suppressed.
    grace_seconds: int = 300
    job_name: str = ""

    def __post_init__(self) -> None:
        if self.grace_seconds < 0:
            raise ValueError("grace_seconds must be >= 0")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")


@dataclasses.dataclass
class GraceResult:
    in_grace: bool
    grace_seconds: int
    first_run_at: Optional[datetime]
    elapsed_seconds: Optional[float]

    def summary(self) -> str:
        if not self.in_grace:
            return "Not in grace period."
        elapsed = self.elapsed_seconds or 0.0
        remaining = max(0.0, self.grace_seconds - elapsed)
        return f"In grace period — {remaining:.0f}s remaining."


def grace_from_dict(d: dict) -> GraceConfig:
    return GraceConfig(
        enabled=bool(d.get("enabled", True)),
        grace_seconds=int(d.get("grace_seconds", 300)),
        job_name=str(d.get("job_name", "")),
    )


def check_grace(config: GraceConfig, history: JobHistory) -> GraceResult:
    """Return a GraceResult indicating whether the job is currently in its grace period."""
    if not config.enabled:
        return GraceResult(
            in_grace=False,
            grace_seconds=config.grace_seconds,
            first_run_at=None,
            elapsed_seconds=None,
        )

    entries = history.for_job(config.job_name)
    if not entries:
        # No history yet — treat as in grace (very first run).
        return GraceResult(
            in_grace=True,
            grace_seconds=config.grace_seconds,
            first_run_at=None,
            elapsed_seconds=None,
        )

    first_run_at = min(e.started_at for e in entries)
    now = datetime.now(timezone.utc)
    elapsed = (now - first_run_at).total_seconds()
    in_grace = elapsed < config.grace_seconds
    return GraceResult(
        in_grace=in_grace,
        grace_seconds=config.grace_seconds,
        first_run_at=first_run_at,
        elapsed_seconds=elapsed,
    )

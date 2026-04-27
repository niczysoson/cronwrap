"""Job maturity tracking — flag jobs that haven't run successfully in a while."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import JobHistory


@dataclass
class MaturityConfig:
    """Configuration for job maturity checks."""
    max_age_hours: float
    job_name: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive")
        if not self.job_name or not self.job_name.strip():
            raise ValueError("job_name must not be empty")


@dataclass
class MaturityResult:
    job_name: str
    last_success: Optional[datetime]
    age_hours: Optional[float]
    is_mature: bool  # True means the job is stale / overdue
    threshold_hours: float

    def summary(self) -> str:
        if not self.is_mature:
            age = f"{self.age_hours:.1f}h ago" if self.age_hours is not None else "never"
            return f"{self.job_name}: OK (last success {age})"
        if self.last_success is None:
            return f"{self.job_name}: STALE (no successful run recorded)"
        return (
            f"{self.job_name}: STALE "
            f"(last success {self.age_hours:.1f}h ago, threshold {self.threshold_hours}h)"
        )


def maturity_from_dict(d: dict) -> MaturityConfig:
    return MaturityConfig(
        max_age_hours=float(d["max_age_hours"]),
        job_name=d["job_name"],
        enabled=bool(d.get("enabled", True)),
    )


def check_maturity(cfg: MaturityConfig, history: JobHistory) -> MaturityResult:
    """Return a MaturityResult indicating whether the job is overdue."""
    if not cfg.enabled:
        return MaturityResult(
            job_name=cfg.job_name,
            last_success=None,
            age_hours=None,
            is_mature=False,
            threshold_hours=cfg.max_age_hours,
        )

    entries = [
        e for e in history.for_job(cfg.job_name) if e.succeeded()
    ]

    if not entries:
        return MaturityResult(
            job_name=cfg.job_name,
            last_success=None,
            age_hours=None,
            is_mature=True,
            threshold_hours=cfg.max_age_hours,
        )

    latest = max(entries, key=lambda e: e.started_at)
    now = datetime.now(tz=timezone.utc)
    age_hours = (now - latest.started_at).total_seconds() / 3600.0
    is_mature = age_hours > cfg.max_age_hours

    return MaturityResult(
        job_name=cfg.job_name,
        last_success=latest.started_at,
        age_hours=round(age_hours, 3),
        is_mature=is_mature,
        threshold_hours=cfg.max_age_hours,
    )

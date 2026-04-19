"""Run limit: cap the total number of times a job may run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwrap.history import JobHistory


@dataclass
class RunLimitConfig:
    max_runs: int
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")


def run_limit_from_dict(data: dict) -> RunLimitConfig:
    return RunLimitConfig(
        max_runs=int(data["max_runs"]),
        enabled=bool(data.get("enabled", True)),
    )


def count_total_runs(job_name: str, history_path: str) -> int:
    """Return total number of completed runs recorded for *job_name*."""
    store = JobHistory(history_path)
    return len(store.for_job(job_name))


def is_run_limit_exceeded(
    config: RunLimitConfig,
    job_name: str,
    history_path: str,
) -> bool:
    """Return True when the job has reached or exceeded its run cap."""
    if not config.enabled:
        return False
    return count_total_runs(job_name, history_path) >= config.max_runs


def run_limit_status(
    config: RunLimitConfig,
    job_name: str,
    history_path: str,
) -> dict:
    total = count_total_runs(job_name, history_path)
    remaining = max(0, config.max_runs - total)
    return {
        "enabled": config.enabled,
        "max_runs": config.max_runs,
        "total_runs": total,
        "remaining": remaining,
        "exceeded": total >= config.max_runs if config.enabled else False,
    }

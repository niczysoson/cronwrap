"""Lightweight metrics collection for cron job runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from cronwrap.history import JobHistory


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_duration_seconds: float = 0.0
    min_duration_seconds: Optional[float] = None
    max_duration_seconds: Optional[float] = None

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def avg_duration_seconds(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.total_duration_seconds / self.total_runs

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": round(self.success_rate, 4),
            "avg_duration_seconds": round(self.avg_duration_seconds, 3),
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
        }


def compute_metrics(job_name: str, history: JobHistory) -> JobMetrics:
    """Compute metrics for a single job from its history."""
    entries = history.get(job_name)
    m = JobMetrics(job_name=job_name)
    for entry in entries:
        m.total_runs += 1
        duration = entry.duration_seconds
        m.total_duration_seconds += duration
        if m.min_duration_seconds is None or duration < m.min_duration_seconds:
            m.min_duration_seconds = duration
        if m.max_duration_seconds is None or duration > m.max_duration_seconds:
            m.max_duration_seconds = duration
        if entry.success:
            m.successful_runs += 1
        else:
            m.failed_runs += 1
    return m


def compute_all_metrics(history: JobHistory) -> List[JobMetrics]:
    """Compute metrics for all jobs tracked in history."""
    names = {e.job_name for e in history._entries}
    return [compute_metrics(name, history) for name in sorted(names)]

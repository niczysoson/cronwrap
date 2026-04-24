"""Track and report run-time variance across job executions."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import HistoryEntry, JobHistory


@dataclass
class VarianceReport:
    job_name: str
    sample_count: int
    mean_seconds: Optional[float]
    stddev_seconds: Optional[float]
    min_seconds: Optional[float]
    max_seconds: Optional[float]
    cv_percent: Optional[float]  # coefficient of variation

    @property
    def is_stable(self) -> bool:
        """Return True when CV is below 25 % (low variance)."""
        if self.cv_percent is None:
            return True
        return self.cv_percent < 25.0

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "sample_count": self.sample_count,
            "mean_seconds": self.mean_seconds,
            "stddev_seconds": self.stddev_seconds,
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "cv_percent": self.cv_percent,
            "is_stable": self.is_stable,
        }


def _durations(entries: List[HistoryEntry]) -> List[float]:
    durations: List[float] = []
    for e in entries:
        if e.started_at and e.finished_at:
            delta = (e.finished_at - e.started_at).total_seconds()
            if delta >= 0:
                durations.append(delta)
    return durations


def compute_variance(job_name: str, history: JobHistory) -> VarianceReport:
    """Compute runtime variance statistics for *job_name*."""
    entries = history.for_job(job_name)
    durations = _durations(entries)
    n = len(durations)

    if n == 0:
        return VarianceReport(
            job_name=job_name,
            sample_count=0,
            mean_seconds=None,
            stddev_seconds=None,
            min_seconds=None,
            max_seconds=None,
            cv_percent=None,
        )

    mean = statistics.mean(durations)
    stddev = statistics.pstdev(durations) if n >= 2 else 0.0
    cv = (stddev / mean * 100.0) if mean > 0 else 0.0

    return VarianceReport(
        job_name=job_name,
        sample_count=n,
        mean_seconds=round(mean, 3),
        stddev_seconds=round(stddev, 3),
        min_seconds=round(min(durations), 3),
        max_seconds=round(max(durations), 3),
        cv_percent=round(cv, 2),
    )


def compute_all_variance(history: JobHistory) -> List[VarianceReport]:
    """Return a variance report for every distinct job in *history*."""
    names = {e.job_name for e in history.all()}
    return [compute_variance(name, history) for name in sorted(names)]

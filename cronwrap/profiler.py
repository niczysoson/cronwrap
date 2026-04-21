"""Job profiling: track CPU time, memory usage, and timing statistics per job."""
from __future__ import annotations

import time
import resource
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProfileSample:
    job_name: str
    started_at: float
    finished_at: Optional[float] = None
    user_cpu_seconds: float = 0.0
    system_cpu_seconds: float = 0.0
    max_rss_kb: int = 0

    @property
    def wall_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return self.finished_at - self.started_at

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "wall_seconds": self.wall_seconds,
            "user_cpu_seconds": self.user_cpu_seconds,
            "system_cpu_seconds": self.system_cpu_seconds,
            "max_rss_kb": self.max_rss_kb,
        }

    @staticmethod
    def from_dict(d: dict) -> "ProfileSample":
        s = ProfileSample(
            job_name=d["job_name"],
            started_at=d["started_at"],
            finished_at=d.get("finished_at"),
            user_cpu_seconds=d.get("user_cpu_seconds", 0.0),
            system_cpu_seconds=d.get("system_cpu_seconds", 0.0),
            max_rss_kb=d.get("max_rss_kb", 0),
        )
        return s


class Profiler:
    """Context-manager profiler for a single job run."""

    def __init__(self, job_name: str):
        self.job_name = job_name
        self._sample: Optional[ProfileSample] = None
        self._ru_start: Optional[resource.struct_rusage] = None

    def __enter__(self) -> "Profiler":
        self._ru_start = resource.getrusage(resource.RUSAGE_CHILDREN)
        self._sample = ProfileSample(
            job_name=self.job_name,
            started_at=time.monotonic(),
        )
        return self

    def __exit__(self, *_) -> None:
        if self._sample is None:
            return
        ru_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        self._sample.finished_at = time.monotonic()
        if self._ru_start is not None:
            self._sample.user_cpu_seconds = round(
                ru_end.ru_utime - self._ru_start.ru_utime, 4
            )
            self._sample.system_cpu_seconds = round(
                ru_end.ru_stime - self._ru_start.ru_stime, 4
            )
        self._sample.max_rss_kb = ru_end.ru_maxrss

    @property
    def sample(self) -> Optional[ProfileSample]:
        return self._sample


def profiler_from_dict(d: dict) -> Profiler:
    """Build a Profiler from a config dict (only needs 'job_name')."""
    return Profiler(job_name=d["job_name"])

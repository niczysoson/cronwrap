"""Job dependency checking — ensure prerequisite jobs succeeded before running."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from cronwrap.history import JobHistory


@dataclass
class DependencyConfig:
    requires: List[str] = field(default_factory=list)
    max_age_seconds: Optional[int] = None  # how recent the success must be

    def __post_init__(self):
        if self.max_age_seconds is not None and self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")


@dataclass
class DependencyResult:
    satisfied: bool
    missing: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.satisfied:
            return "All dependencies satisfied."
        return "Unsatisfied dependencies: " + ", ".join(self.missing)


def dependency_from_dict(d: dict) -> DependencyConfig:
    return DependencyConfig(
        requires=d.get("requires", []),
        max_age_seconds=d.get("max_age_seconds"),
    )


def check_dependencies(
    config: DependencyConfig,
    history: JobHistory,
) -> DependencyResult:
    """Return a DependencyResult indicating which required jobs have not succeeded."""
    import time

    missing = []
    for job_name in config.requires:
        entries = history.get(job_name)
        successes = [e for e in entries if e.succeeded]
        if not successes:
            missing.append(job_name)
            continue
        if config.max_age_seconds is not None:
            latest = max(successes, key=lambda e: e.started_at)
            age = time.time() - latest.started_at
            if age > config.max_age_seconds:
                missing.append(job_name)
    return DependencyResult(satisfied=len(missing) == 0, missing=missing)

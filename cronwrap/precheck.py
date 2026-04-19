"""Pre-flight checks before running a cron job."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PrecheckResult:
    passed: bool
    failures: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.passed:
            return "All pre-checks passed."
        return "Pre-checks failed: " + "; ".join(self.failures)


@dataclass
class PrecheckConfig:
    required_commands: List[str] = field(default_factory=list)
    required_env: List[str] = field(default_factory=list)
    min_disk_mb: Optional[int] = None

    def __post_init__(self) -> None:
        if self.min_disk_mb is not None and self.min_disk_mb < 0:
            raise ValueError("min_disk_mb must be >= 0")


def precheck_from_dict(data: dict) -> PrecheckConfig:
    return PrecheckConfig(
        required_commands=data.get("required_commands", []),
        required_env=data.get("required_env", []),
        min_disk_mb=data.get("min_disk_mb"),
    )


def run_prechecks(cfg: PrecheckConfig) -> PrecheckResult:
    import os

    failures: List[str] = []

    for cmd in cfg.required_commands:
        if shutil.which(cmd) is None:
            failures.append(f"command not found: {cmd}")

    for var in cfg.required_env:
        if not os.environ.get(var):
            failures.append(f"env var not set: {var}")

    if cfg.min_disk_mb is not None:
        stat = shutil.disk_usage("/")
        free_mb = stat.free // (1024 * 1024)
        if free_mb < cfg.min_disk_mb:
            failures.append(
                f"insufficient disk space: {free_mb} MB free, {cfg.min_disk_mb} MB required"
            )

    return PrecheckResult(passed=len(failures) == 0, failures=failures)

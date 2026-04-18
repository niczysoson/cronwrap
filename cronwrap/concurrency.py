"""Concurrency limit: cap how many instances of a job run simultaneously."""
from __future__ import annotations

import os
import glob
import time
from dataclasses import dataclass, field
from pathlib import Path


class ConcurrencyError(Exception):
    """Raised when the concurrency limit is exceeded."""


@dataclass
class ConcurrencyConfig:
    max_concurrent: int = 1
    lock_dir: str = "/tmp/cronwrap_concurrency"

    def __post_init__(self) -> None:
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")


def concurrency_from_dict(d: dict) -> ConcurrencyConfig:
    return ConcurrencyConfig(
        max_concurrent=int(d.get("max_concurrent", 1)),
        lock_dir=d.get("lock_dir", "/tmp/cronwrap_concurrency"),
    )


def _slot_paths(job_name: str, lock_dir: str) -> list[str]:
    pattern = os.path.join(lock_dir, f"{job_name}.*.lock")
    return glob.glob(pattern)


def _clean_stale(paths: list[str], ttl: int = 3600) -> list[str]:
    now = time.time()
    live = []
    for p in paths:
        try:
            if now - os.path.getmtime(p) < ttl:
                live.append(p)
            else:
                os.remove(p)
        except OSError:
            pass
    return live


def acquire_slot(job_name: str, cfg: ConcurrencyConfig) -> str:
    """Acquire a concurrency slot; returns the lock-file path."""
    Path(cfg.lock_dir).mkdir(parents=True, exist_ok=True)
    existing = _clean_stale(_slot_paths(job_name, cfg.lock_dir))
    if len(existing) >= cfg.max_concurrent:
        raise ConcurrencyError(
            f"Job '{job_name}' already has {len(existing)}/{cfg.max_concurrent} "
            "concurrent instance(s) running."
        )
    slot = os.path.join(cfg.lock_dir, f"{job_name}.{os.getpid()}.lock")
    Path(slot).touch()
    return slot


def release_slot(slot_path: str) -> None:
    try:
        os.remove(slot_path)
    except OSError:
        pass


def current_count(job_name: str, cfg: ConcurrencyConfig) -> int:
    return len(_clean_stale(_slot_paths(job_name, cfg.lock_dir)))

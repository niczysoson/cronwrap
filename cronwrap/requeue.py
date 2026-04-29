"""Requeue support — mark a job for forced re-execution on next run.

A job can be 'requeued' by writing a small sentinel file.  The runner
checks for the sentinel before applying throttle / debounce guards and,
if present, removes the file and proceeds regardless of those guards.
"""
from __future__ import annotations

import dataclasses
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_DEFAULT_DIR = Path(os.environ.get("CRONWRAP_STATE_DIR", "/tmp/cronwrap")) / "requeue"


@dataclasses.dataclass
class RequeueConfig:
    enabled: bool = True
    state_dir: str = str(_DEFAULT_DIR)

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if not self.state_dir or not isinstance(self.state_dir, str):
            raise ValueError("state_dir must be a non-empty string")

    def _sentinel_path(self, job_name: str) -> Path:
        return Path(self.state_dir) / f"{job_name}.requeue"

    def is_queued(self, job_name: str) -> bool:
        """Return True if a requeue sentinel exists for *job_name*."""
        if not self.enabled:
            return False
        return self._sentinel_path(job_name).exists()

    def enqueue(self, job_name: str, reason: str = "") -> Path:
        """Write a sentinel file requesting re-execution of *job_name*."""
        path = self._sentinel_path(job_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "job": job_name,
            "reason": reason,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(payload))
        return path

    def dequeue(self, job_name: str) -> Optional[dict]:
        """Remove and return the sentinel payload, or None if absent."""
        path = self._sentinel_path(job_name)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            payload = {}
        path.unlink(missing_ok=True)
        return payload


def requeue_from_dict(data: dict) -> RequeueConfig:
    return RequeueConfig(
        enabled=data.get("enabled", True),
        state_dir=data.get("state_dir", str(_DEFAULT_DIR)),
    )

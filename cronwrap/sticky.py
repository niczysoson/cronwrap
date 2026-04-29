"""Sticky failure tracking — remember the last failure and suppress re-alerts.

A job is considered "sticky" when it has failed and not yet recovered.
Once a success is recorded the sticky flag is cleared.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class StickyConfig:
    enabled: bool = True
    state_dir: str = "/tmp/cronwrap/sticky"

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if not self.state_dir:
            raise ValueError("state_dir must not be empty")

    def _state_path(self, job_name: str) -> Path:
        return Path(self.state_dir) / f"{job_name}.json"

    def is_sticky(self, job_name: str) -> bool:
        """Return True if the job is currently in a failed/sticky state."""
        if not self.enabled:
            return False
        p = self._state_path(job_name)
        return p.exists()

    def mark_failed(self, job_name: str, exit_code: int = 1) -> None:
        """Record that the job has failed (sets the sticky flag)."""
        if not self.enabled:
            return
        p = self._state_path(job_name)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "job": job_name,
            "exit_code": exit_code,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        p.write_text(json.dumps(payload))

    def clear(self, job_name: str) -> None:
        """Clear the sticky flag (job recovered)."""
        p = self._state_path(job_name)
        if p.exists():
            p.unlink()

    def state(self, job_name: str) -> Optional[dict]:
        """Return the raw state dict if sticky, else None."""
        p = self._state_path(job_name)
        if not p.exists():
            return None
        return json.loads(p.read_text())


def sticky_from_dict(data: dict) -> StickyConfig:
    return StickyConfig(
        enabled=data.get("enabled", True),
        state_dir=data.get("state_dir", "/tmp/cronwrap/sticky"),
    )

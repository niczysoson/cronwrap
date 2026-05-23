"""Manual trigger support — allows a job to be flagged for immediate execution."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class TriggerConfig:
    enabled: bool = True
    state_dir: str = "/tmp/cronwrap/triggers"

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if not isinstance(self.state_dir, str) or not self.state_dir.strip():
            raise ValueError("state_dir must be a non-empty string")

    def _trigger_path(self, job_name: str) -> Path:
        return Path(self.state_dir) / f"{job_name}.trigger"

    def is_triggered(self, job_name: str) -> bool:
        """Return True if a manual trigger sentinel exists for *job_name*."""
        if not self.enabled:
            return False
        return self._trigger_path(job_name).exists()

    def set_trigger(self, job_name: str) -> None:
        """Create a trigger sentinel for *job_name*."""
        if not self.enabled:
            return
        path = self._trigger_path(job_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"job": job_name, "triggered_at": datetime.now(timezone.utc).isoformat()}
        path.write_text(json.dumps(payload))

    def clear_trigger(self, job_name: str) -> None:
        """Remove the trigger sentinel for *job_name* if it exists."""
        path = self._trigger_path(job_name)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def trigger_info(self, job_name: str) -> Optional[dict]:
        """Return the stored trigger payload or None."""
        path = self._trigger_path(job_name)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None


def trigger_from_dict(data: dict) -> TriggerConfig:
    return TriggerConfig(
        enabled=data.get("enabled", True),
        state_dir=data.get("state_dir", "/tmp/cronwrap/triggers"),
    )

"""Pinned jobs: prevent a job from running if its config hash has changed."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PinnedConfig:
    job_name: str
    config_dict: dict
    pin_dir: str = "/tmp/cronwrap/pins"
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.job_name:
            raise ValueError("job_name must not be empty")

    def _pin_path(self) -> Path:
        return Path(self.pin_dir) / f"{self.job_name}.pin"

    def current_hash(self) -> str:
        serialised = json.dumps(self.config_dict, sort_keys=True)
        return hashlib.sha256(serialised.encode()).hexdigest()

    def saved_hash(self) -> Optional[str]:
        p = self._pin_path()
        if p.exists():
            return p.read_text().strip()
        return None

    def save(self) -> None:
        p = self._pin_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.current_hash())

    def clear(self) -> None:
        self._pin_path().unlink(missing_ok=True)

    def is_changed(self) -> bool:
        """Return True if config has changed since last pin (or never pinned)."""
        if not self.enabled:
            return False
        saved = self.saved_hash()
        if saved is None:
            return False
        return saved != self.current_hash()


def pinned_from_dict(d: dict) -> PinnedConfig:
    return PinnedConfig(
        job_name=d["job_name"],
        config_dict=d.get("config", {}),
        pin_dir=d.get("pin_dir", "/tmp/cronwrap/pins"),
        enabled=d.get("enabled", True),
    )

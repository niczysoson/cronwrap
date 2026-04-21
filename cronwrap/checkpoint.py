"""Checkpoint support: persist and restore step progress for multi-step jobs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


_DEFAULT_DIR = Path(os.environ.get("CRONWRAP_CHECKPOINT_DIR", "/tmp/cronwrap/checkpoints"))


@dataclass
class Checkpoint:
    job_name: str
    completed_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_done(self, step: str) -> None:
        if step not in self.completed_steps:
            self.completed_steps.append(step)

    def is_done(self, step: str) -> bool:
        return step in self.completed_steps

    def reset(self) -> None:
        """Clear all completed steps and metadata, restarting progress from scratch."""
        self.completed_steps.clear()
        self.metadata.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_name": self.job_name,
            "completed_steps": self.completed_steps,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Checkpoint":
        return cls(
            job_name=d["job_name"],
            completed_steps=d.get("completed_steps", []),
            metadata=d.get("metadata", {}),
        )


def _checkpoint_path(job_name: str, directory: Path) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return directory / f"{safe}.json"


def load_checkpoint(job_name: str, directory: Path = _DEFAULT_DIR) -> Optional[Checkpoint]:
    path = _checkpoint_path(job_name, directory)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return Checkpoint.from_dict(json.load(f))
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"Checkpoint file for '{job_name}' is corrupt or invalid: {path}") from exc


def save_checkpoint(cp: Checkpoint, directory: Path = _DEFAULT_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(cp.job_name, directory)
    with open(path, "w") as f:
        json.dump(cp.to_dict(), f, indent=2)


def clear_checkpoint(job_name: str, directory: Path = _DEFAULT_DIR) -> bool:
    path = _checkpoint_path(job_name, directory)
    if path.exists():
        path.unlink()
        return True
    return False

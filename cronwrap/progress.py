"""Step-level progress tracking for multi-step cron jobs."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class StepProgress:
    name: str
    status: str  # pending | running | done | failed
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    message: str = ""

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            return round(self.finished_at - self.started_at, 3)
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StepProgress":
        return cls(**d)


@dataclass
class JobProgress:
    job_name: str
    steps: List[StepProgress] = field(default_factory=list)

    def start_step(self, name: str) -> StepProgress:
        step = StepProgress(name=name, status="running", started_at=time.time())
        self.steps.append(step)
        return step

    def finish_step(self, name: str, success: bool = True, message: str = "") -> None:
        for step in self.steps:
            if step.name == name and step.status == "running":
                step.status = "done" if success else "failed"
                step.finished_at = time.time()
                step.message = message
                return
        raise KeyError(f"No running step named {name!r}")

    def to_dict(self) -> dict:
        return {"job_name": self.job_name, "steps": [s.to_dict() for s in self.steps]}

    @classmethod
    def from_dict(cls, d: dict) -> "JobProgress":
        return cls(
            job_name=d["job_name"],
            steps=[StepProgress.from_dict(s) for s in d.get("steps", [])],
        )


def save_progress(progress: JobProgress, path: Path) -> None:
    path.write_text(json.dumps(progress.to_dict(), indent=2))


def load_progress(path: Path) -> Optional[JobProgress]:
    if not path.exists():
        return None
    return JobProgress.from_dict(json.loads(path.read_text()))

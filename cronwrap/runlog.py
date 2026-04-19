"""Per-job structured run log with start/end timestamps and exit codes."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class RunLogEntry:
    job_name: str
    command: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""

    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def succeeded(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "command": self.command,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }

    @staticmethod
    def from_dict(d: dict) -> "RunLogEntry":
        return RunLogEntry(
            job_name=d["job_name"],
            command=d["command"],
            started_at=datetime.fromisoformat(d["started_at"]),
            finished_at=datetime.fromisoformat(d["finished_at"]) if d.get("finished_at") else None,
            exit_code=d.get("exit_code"),
            stdout=d.get("stdout", ""),
            stderr=d.get("stderr", ""),
        )


class RunLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[dict]:
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return json.load(f)

    def _save(self, entries: List[dict]) -> None:
        with open(self.path, "w") as f:
            json.dump(entries, f, indent=2)

    def append(self, entry: RunLogEntry) -> None:
        entries = self._load()
        entries.append(entry.to_dict())
        self._save(entries)

    def all(self) -> List[RunLogEntry]:
        return [RunLogEntry.from_dict(d) for d in self._load()]

    def for_job(self, job_name: str) -> List[RunLogEntry]:
        return [e for e in self.all() if e.job_name == job_name]

    def last(self, job_name: str) -> Optional[RunLogEntry]:
        entries = self.for_job(job_name)
        return entries[-1] if entries else None

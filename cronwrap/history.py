"""Persistent job run history."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class HistoryEntry:
    job_name: str
    started_at: str
    duration_seconds: float
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @staticmethod
    def success(job_name: str, started_at: str, duration: float, stdout: str = "", tags: Optional[List[str]] = None) -> "HistoryEntry":
        return HistoryEntry(job_name, started_at, duration, 0, stdout, tags=tags or [])

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            job_name=d["job_name"],
            started_at=d["started_at"],
            duration_seconds=d["duration_seconds"],
            exit_code=d["exit_code"],
            stdout=d.get("stdout", ""),
            stderr=d.get("stderr", ""),
            tags=d.get("tags", []),
        )

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "tags": self.tags,
        }


class JobHistory:
    def __init__(self, path: str):
        self.path = path
        self.entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                data = json.load(f)
            self.entries = [HistoryEntry.from_dict(d) for d in data]

    def _save(self):
        with open(self.path, "w") as f:
            json.dump([e.to_dict() for e in self.entries], f, indent=2)

    def record(self, entry: HistoryEntry):
        self.entries.append(entry)
        self._save()

    def for_job(self, job_name: str) -> List[HistoryEntry]:
        return [e for e in self.entries if e.job_name == job_name]

    def filter_by_job_name(self, job_name: str) -> List[HistoryEntry]:
        return self.for_job(job_name)

    def last_for_job(self, job_name: str) -> Optional[HistoryEntry]:
        """Return the most recent history entry for a given job, or None if not found."""
        entries = self.for_job(job_name)
        return entries[-1] if entries else None

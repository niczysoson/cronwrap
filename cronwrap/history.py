"""Job execution history tracking using a simple JSON file store."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class HistoryEntry:
    job_name: str
    command: str
    started_at: str
    finished_at: str
    exit_code: int
    attempts: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**data)


class JobHistory:
    def __init__(self, path: str = ".cronwrap_history.json"):
        self.path = path
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    raw = json.load(f)
                self._entries = [HistoryEntry.from_dict(e) for e in raw]
            except (json.JSONDecodeError, KeyError, TypeError):
                self._entries = []

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([asdict(e) for e in self._entries], f, indent=2)

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        self._save()

    def last(self, job_name: str) -> Optional[HistoryEntry]:
        matches = [e for e in self._entries if e.job_name == job_name]
        return matches[-1] if matches else None

    def all(self, job_name: Optional[str] = None) -> List[HistoryEntry]:
        if job_name:
            return [e for e in self._entries if e.job_name == job_name]
        return list(self._entries)

    def recent_failures(self, job_name: str, limit: int = 5) -> List[HistoryEntry]:
        entries = [e for e in self._entries if e.job_name == job_name and not e.success]
        return entries[-limit:]

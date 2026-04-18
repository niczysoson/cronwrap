"""Job run history tracking with optional file persistence."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DT_FMT = "%Y-%m-%dT%H:%M:%S"


@dataclass
class HistoryEntry:
    job_name: str
    started_at: datetime
    duration_seconds: float
    exit_code: int
    success: bool
    stdout: str = ""
    stderr: str = ""

    @staticmethod
    def success(job_name: str, started_at: datetime, duration: float, stdout: str = "") -> "HistoryEntry":
        return HistoryEntry(job_name, started_at, duration, 0, True, stdout)

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        d = dict(d)
        d["started_at"] = datetime.strptime(d["started_at"], DT_FMT)
        return HistoryEntry(**d)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["started_at"] = self.started_at.strftime(DT_FMT)
        return d


class JobHistory:
    def __init__(self, filepath: Optional[str] = None):
        self._filepath = Path(filepath) if filepath else None
        self._entries: List[HistoryEntry] = []
        if self._filepath and self._filepath.exists():
            self._load()

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        if self._filepath:
            self._save()

    def get(self, job_name: str, limit: int = 100) -> List[HistoryEntry]:
        matches = [e for e in self._entries if e.job_name == job_name]
        return list(reversed(matches[-limit:]))

    def list_jobs(self) -> List[str]:
        return list({e.job_name for e in self._entries})

    def filter_by_status(self, success: bool) -> List[HistoryEntry]:
        return [e for e in self._entries if e.success == success]

    def _save(self) -> None:
        assert self._filepath
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        with self._filepath.open("w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def _load(self) -> None:
        assert self._filepath
        with self._filepath.open() as f:
            self._entries = [HistoryEntry.from_dict(d) for d in json.load(f)]

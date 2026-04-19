"""Simple structured event log for cron job lifecycle events."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class EventEntry:
    job_name: str
    event: str  # e.g. "start", "success", "failure", "retry", "skip"
    timestamp: datetime
    detail: str = ""
    exit_code: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "detail": self.detail,
            "exit_code": self.exit_code,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EventEntry":
        return cls(
            job_name=d["job_name"],
            event=d["event"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            detail=d.get("detail", ""),
            exit_code=d.get("exit_code"),
        )


class EventLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, job_name: str, event: str, detail: str = "", exit_code: Optional[int] = None) -> EventEntry:
        entry = EventEntry(
            job_name=job_name,
            event=event,
            timestamp=datetime.now(tz=timezone.utc),
            detail=detail,
            exit_code=exit_code,
        )
        with self.path.open("a") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def all(self) -> List[EventEntry]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                entries.append(EventEntry.from_dict(json.loads(line)))
        return entries

    def for_job(self, job_name: str) -> List[EventEntry]:
        return [e for e in self.all() if e.job_name == job_name]

    def for_event(self, event: str) -> List[EventEntry]:
        return [e for e in self.all() if e.event == event]

    def last(self, job_name: str) -> Optional[EventEntry]:
        entries = self.for_job(job_name)
        return entries[-1] if entries else None

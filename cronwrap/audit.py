"""Audit log: append-only record of every job execution event."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEvent:
    job_name: str
    event: str          # started | succeeded | failed | retry | throttled | locked
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    detail: Optional[str] = None
    exit_code: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "event": self.event,
            "timestamp": self.timestamp,
            "detail": self.detail,
            "exit_code": self.exit_code,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditEvent":
        return AuditEvent(
            job_name=d["job_name"],
            event=d["event"],
            timestamp=d["timestamp"],
            detail=d.get("detail"),
            exit_code=d.get("exit_code"),
        )


class AuditLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> None:
        with self.path.open("a") as fh:
            fh.write(json.dumps(event.to_dict()) + "\n")

    def read_all(self) -> List[AuditEvent]:
        if not self.path.exists():
            return []
        events = []
        with self.path.open() as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(AuditEvent.from_dict(json.loads(line)))
        return events

    def filter(self, job_name: Optional[str] = None, event: Optional[str] = None) -> List[AuditEvent]:
        results = self.read_all()
        if job_name:
            results = [e for e in results if e.job_name == job_name]
        if event:
            results = [e for e in results if e.event == event]
        return results


def audit_log_from_env(default: str = ".cronwrap/audit.log") -> AuditLog:
    path = os.environ.get("CRONWRAP_AUDIT_LOG", default)
    return AuditLog(path)

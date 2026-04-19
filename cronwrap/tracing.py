"""Lightweight span-based tracing for cron job execution."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Span:
    name: str
    job_name: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    status: str = "running"  # running | ok | error
    metadata: dict = field(default_factory=dict)

    def finish(self, status: str = "ok") -> None:
        self.finished_at = time.time()
        self.status = status

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return round(self.finished_at - self.started_at, 4)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "job_name": self.job_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Span":
        s = cls(name=d["name"], job_name=d["job_name"], trace_id=d["trace_id"],
                span_id=d["span_id"], started_at=d["started_at"],
                finished_at=d.get("finished_at"), status=d.get("status", "ok"),
                metadata=d.get("metadata", {}))
        return s


class TraceStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, span: Span) -> None:
        with self.path.open("a") as fh:
            fh.write(json.dumps(span.to_dict()) + "\n")

    def all(self) -> List[Span]:
        if not self.path.exists():
            return []
        spans = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                spans.append(Span.from_dict(json.loads(line)))
        return spans

    def for_job(self, job_name: str) -> List[Span]:
        return [s for s in self.all() if s.job_name == job_name]

    def for_trace(self, trace_id: str) -> List[Span]:
        return [s for s in self.all() if s.trace_id == trace_id]

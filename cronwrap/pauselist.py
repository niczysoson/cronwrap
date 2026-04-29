"""Pause/resume support for cron jobs.

Allows a job to be temporarily paused so that cronwrap skips execution
without removing the job from the schedule.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class PauseEntry:
    job_name: str
    paused_at: datetime
    reason: str = ""
    resume_at: Optional[datetime] = None

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if the pause is currently in effect."""
        now = now or datetime.now(timezone.utc)
        if self.resume_at is not None:
            return now < self.resume_at
        return True

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "paused_at": self.paused_at.isoformat(),
            "reason": self.reason,
            "resume_at": self.resume_at.isoformat() if self.resume_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PauseEntry":
        return cls(
            job_name=data["job_name"],
            paused_at=datetime.fromisoformat(data["paused_at"]),
            reason=data.get("reason", ""),
            resume_at=(
                datetime.fromisoformat(data["resume_at"])
                if data.get("resume_at")
                else None
            ),
        )


class PauseStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            return json.load(fh)

    def _save(self, records: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(records, fh, indent=2)

    def pause(self, entry: PauseEntry) -> None:
        """Add or replace a pause entry for the given job."""
        records = [r for r in self._load() if r["job_name"] != entry.job_name]
        records.append(entry.to_dict())
        self._save(records)

    def resume(self, job_name: str) -> None:
        """Remove any pause entry for the given job."""
        records = [r for r in self._load() if r["job_name"] != job_name]
        self._save(records)

    def get(self, job_name: str) -> Optional[PauseEntry]:
        for r in self._load():
            if r["job_name"] == job_name:
                return PauseEntry.from_dict(r)
        return None

    def is_paused(self, job_name: str, now: Optional[datetime] = None) -> bool:
        entry = self.get(job_name)
        return entry is not None and entry.is_active(now)

    def all_active(self, now: Optional[datetime] = None) -> list[PauseEntry]:
        return [
            PauseEntry.from_dict(r)
            for r in self._load()
            if PauseEntry.from_dict(r).is_active(now)
        ]

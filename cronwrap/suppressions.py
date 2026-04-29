"""Suppression rules: temporarily silence alerts/notifications for a job."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class SuppressionRule:
    job_name: str
    reason: str
    expires_at: datetime  # UTC
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "reason": self.reason,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuppressionRule":
        return cls(
            job_name=d["job_name"],
            reason=d["reason"],
            expires_at=datetime.fromisoformat(d["expires_at"]),
            created_at=datetime.fromisoformat(d["created_at"]),
        )


class SuppressionStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def _load(self) -> List[SuppressionRule]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            return [SuppressionRule.from_dict(e) for e in json.load(fh)]

    def _save(self, rules: List[SuppressionRule]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump([r.to_dict() for r in rules], fh, indent=2)

    def add(self, rule: SuppressionRule) -> None:
        rules = self._load()
        rules.append(rule)
        self._save(rules)

    def remove_expired(self, now: Optional[datetime] = None) -> int:
        rules = self._load()
        active = [r for r in rules if r.is_active(now)]
        removed = len(rules) - len(active)
        if removed:
            self._save(active)
        return removed

    def is_suppressed(self, job_name: str, now: Optional[datetime] = None) -> bool:
        return any(
            r.job_name == job_name and r.is_active(now) for r in self._load()
        )

    def active_for_job(self, job_name: str, now: Optional[datetime] = None) -> List[SuppressionRule]:
        return [r for r in self._load() if r.job_name == job_name and r.is_active(now)]

    def all_active(self, now: Optional[datetime] = None) -> List[SuppressionRule]:
        return [r for r in self._load() if r.is_active(now)]

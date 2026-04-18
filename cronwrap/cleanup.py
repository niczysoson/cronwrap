"""Cleanup old history and audit entries based on retention policy."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwrap.history import JobHistory
from cronwrap.audit import AuditLog


@dataclass
class RetentionPolicy:
    max_age_days: int = 30
    max_entries: int = 500
    job_name: Optional[str] = None  # None means apply to all

    def __post_init__(self):
        if self.max_age_days < 1:
            raise ValueError("max_age_days must be >= 1")
        if self.max_entries < 1:
            raise ValueError("max_entries must be >= 1")

    @classmethod
    def from_dict(cls, d: dict) -> "RetentionPolicy":
        return cls(
            max_age_days=int(d.get("max_age_days", 30)),
            max_entries=int(d.get("max_entries", 500)),
            job_name=d.get("job_name"),
        )

    def to_dict(self) -> dict:
        return {
            "max_age_days": self.max_age_days,
            "max_entries": self.max_entries,
            "job_name": self.job_name,
        }


def _cutoff(max_age_days: int) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)


def purge_history(history: JobHistory, policy: RetentionPolicy) -> int:
    """Remove old/excess history entries. Returns number of entries removed."""
    entries = history.get_all()
    if policy.job_name:
        entries = [e for e in entries if e.job_name == policy.job_name]
    other = [e for e in history.get_all() if e not in entries]

    cutoff = _cutoff(policy.max_age_days)
    kept = [e for e in entries if e.started_at >= cutoff]
    kept.sort(key=lambda e: e.started_at, reverse=True)
    kept = kept[: policy.max_entries]

    removed = len(entries) - len(kept)
    history._entries = other + kept  # type: ignore[attr-defined]
    return removed


def purge_audit(audit: AuditLog, policy: RetentionPolicy) -> int:
    """Remove old audit events. Returns number of events removed."""
    cutoff = _cutoff(policy.max_age_days)
    events = audit.read(job_name=policy.job_name)
    all_events = audit.read()
    other = [e for e in all_events if e not in events]

    kept = [e for e in events if e.timestamp >= cutoff]
    kept.sort(key=lambda e: e.timestamp, reverse=True)
    kept = kept[: policy.max_entries]

    removed = len(events) - len(kept)
    audit._events = other + kept  # type: ignore[attr-defined]
    return removed

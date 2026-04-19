"""High-water mark tracking: record peak resource usage per job."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class WatermarkEntry:
    job_name: str
    peak_duration_seconds: float
    peak_output_bytes: int
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "peak_duration_seconds": self.peak_duration_seconds,
            "peak_output_bytes": self.peak_output_bytes,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WatermarkEntry":
        return cls(
            job_name=d["job_name"],
            peak_duration_seconds=float(d["peak_duration_seconds"]),
            peak_output_bytes=int(d["peak_output_bytes"]),
            recorded_at=d.get("recorded_at", ""),
        )


class WatermarkStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._data: Dict[str, WatermarkEntry] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path) as fh:
                raw = json.load(fh)
            self._data = {k: WatermarkEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as fh:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, fh, indent=2)

    def update(self, job_name: str, duration_seconds: float, output_bytes: int) -> bool:
        """Update watermark if new values exceed stored peaks. Returns True if updated."""
        existing = self._data.get(job_name)
        if existing is None:
            self._data[job_name] = WatermarkEntry(job_name, duration_seconds, output_bytes)
            self._save()
            return True
        changed = False
        if duration_seconds > existing.peak_duration_seconds:
            existing.peak_duration_seconds = duration_seconds
            changed = True
        if output_bytes > existing.peak_output_bytes:
            existing.peak_output_bytes = output_bytes
            changed = True
        if changed:
            existing.recorded_at = datetime.now(timezone.utc).isoformat()
            self._save()
        return changed

    def get(self, job_name: str) -> Optional[WatermarkEntry]:
        return self._data.get(job_name)

    def all(self) -> List[WatermarkEntry]:
        return list(self._data.values())

    def reset(self, job_name: str) -> bool:
        if job_name in self._data:
            del self._data[job_name]
            self._save()
            return True
        return False

"""Job output snapshot — capture and compare stdout/stderr across runs."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Snapshot:
    job_name: str
    captured_at: datetime
    stdout_hash: str
    stderr_hash: str
    stdout: str
    stderr: str

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "captured_at": self.captured_at.isoformat(),
            "stdout_hash": self.stdout_hash,
            "stderr_hash": self.stderr_hash,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        return cls(
            job_name=d["job_name"],
            captured_at=datetime.fromisoformat(d["captured_at"]),
            stdout_hash=d["stdout_hash"],
            stderr_hash=d["stderr_hash"],
            stdout=d["stdout"],
            stderr=d["stderr"],
        )

    def changed_since(self, other: "Snapshot") -> bool:
        return self.stdout_hash != other.stdout_hash or self.stderr_hash != other.stderr_hash


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def make_snapshot(job_name: str, stdout: str, stderr: str) -> Snapshot:
    return Snapshot(
        job_name=job_name,
        captured_at=datetime.now(timezone.utc),
        stdout_hash=_sha256(stdout),
        stderr_hash=_sha256(stderr),
        stdout=stdout,
        stderr=stderr,
    )


class SnapshotStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._data: dict[str, dict] = {}
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, job_name: str) -> Optional[Snapshot]:
        entry = self._data.get(job_name)
        return Snapshot.from_dict(entry) if entry else None

    def save(self, snapshot: Snapshot) -> None:
        self._data[snapshot.job_name] = snapshot.to_dict()
        self._save()

    def delete(self, job_name: str) -> None:
        self._data.pop(job_name, None)
        self._save()

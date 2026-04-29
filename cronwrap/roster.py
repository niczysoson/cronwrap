"""Job roster — tracks which jobs are registered and their metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RosterEntry:
    name: str
    command: str
    schedule: str
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "command": self.command,
            "schedule": self.schedule,
            "tags": self.tags,
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RosterEntry":
        return cls(
            name=d["name"],
            command=d["command"],
            schedule=d["schedule"],
            tags=d.get("tags", []),
            enabled=d.get("enabled", True),
            description=d.get("description", ""),
        )


class Roster:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._entries: Dict[str, RosterEntry] = {}
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text())
        for item in data:
            e = RosterEntry.from_dict(item)
            self._entries[e.name] = e

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([e.to_dict() for e in self._entries.values()], indent=2))

    def register(self, entry: RosterEntry) -> None:
        self._entries[entry.name] = entry
        self._save()

    def unregister(self, name: str) -> bool:
        if name in self._entries:
            del self._entries[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> Optional[RosterEntry]:
        return self._entries.get(name)

    def all(self) -> List[RosterEntry]:
        return list(self._entries.values())

    def enabled(self) -> List[RosterEntry]:
        return [e for e in self._entries.values() if e.enabled]

    def by_tag(self, tag: str) -> List[RosterEntry]:
        return [e for e in self._entries.values() if tag in e.tags]


def roster_from_dict(d: dict, roster_dir: str = "/tmp/cronwrap") -> Roster:
    path = Path(d.get("roster_file", os.path.join(roster_dir, "roster.json")))
    return Roster(path)

"""Heartbeat: periodically write a timestamp so external monitors can detect stalled jobs."""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class HeartbeatConfig:
    job_name: str
    interval_seconds: float = 30.0
    directory: str = "/tmp/cronwrap/heartbeats"
    max_age_seconds: Optional[float] = None  # if set, used for staleness check

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_age_seconds is not None and self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")

    @property
    def beat_path(self) -> Path:
        return Path(self.directory) / f"{self.job_name}.json"


def heartbeat_from_dict(d: dict) -> HeartbeatConfig:
    return HeartbeatConfig(
        job_name=d["job_name"],
        interval_seconds=float(d.get("interval_seconds", 30.0)),
        directory=d.get("directory", "/tmp/cronwrap/heartbeats"),
        max_age_seconds=float(d["max_age_seconds"]) if "max_age_seconds" in d else None,
    )


def write_beat(cfg: HeartbeatConfig) -> None:
    """Write a heartbeat timestamp to disk."""
    path = cfg.beat_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"job": cfg.job_name, "ts": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(payload))


def read_beat(cfg: HeartbeatConfig) -> Optional[datetime]:
    """Return the last heartbeat time, or None if not found."""
    try:
        data = json.loads(cfg.beat_path.read_text())
        return datetime.fromisoformat(data["ts"])
    except (FileNotFoundError, KeyError, ValueError):
        return None


def is_stale(cfg: HeartbeatConfig) -> bool:
    """Return True if the heartbeat is older than max_age_seconds."""
    if cfg.max_age_seconds is None:
        return False
    last = read_beat(cfg)
    if last is None:
        return True
    age = (datetime.now(timezone.utc) - last).total_seconds()
    return age > cfg.max_age_seconds


class HeartbeatThread:
    """Background thread that writes heartbeats at a fixed interval."""

    def __init__(self, cfg: HeartbeatConfig) -> None:
        self._cfg = cfg
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        write_beat(self._cfg)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self._cfg.interval_seconds + 1)

    def _run(self) -> None:
        while not self._stop.wait(self._cfg.interval_seconds):
            write_beat(self._cfg)

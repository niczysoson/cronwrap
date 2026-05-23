"""Track how many times a job has been pinned/held back and enforce a maximum."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwrap.history import HistoryStore


@dataclass
class PinCountConfig:
    """Configuration for pin-count enforcement."""
    enabled: bool = True
    job_name: str = ""
    max_pins: int = 3
    window_seconds: int = 3600

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
        if self.max_pins < 1:
            raise ValueError("max_pins must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


@dataclass
class PinCountResult:
    """Result of a pin-count check."""
    pinned_count: int
    max_pins: int
    exceeded: bool
    message: str = field(default="")

    def summary(self) -> str:
        return self.message or (
            f"pinned {self.pinned_count}/{self.max_pins} times in window"
        )


def pincount_from_dict(data: dict) -> PinCountConfig:
    """Build a PinCountConfig from a plain dict."""
    return PinCountConfig(
        enabled=bool(data.get("enabled", True)),
        job_name=str(data.get("job_name", "")),
        max_pins=int(data.get("max_pins", 3)),
        window_seconds=int(data.get("window_seconds", 3600)),
    )


def count_pins_in_window(
    job_name: str,
    window_seconds: int,
    store: HistoryStore,
) -> int:
    """Return how many *failed* (pinned) runs exist within the rolling window."""
    import datetime
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=window_seconds)
    entries = store.for_job(job_name)
    return sum(
        1 for e in entries
        if not e.succeeded and e.finished_at and e.finished_at >= cutoff
    )


def is_pin_count_exceeded(
    cfg: PinCountConfig,
    store: HistoryStore,
) -> PinCountResult:
    """Check whether the job has exceeded its allowed pin count."""
    if not cfg.enabled:
        return PinCountResult(
            pinned_count=0,
            max_pins=cfg.max_pins,
            exceeded=False,
            message="pin-count enforcement disabled",
        )
    count = count_pins_in_window(cfg.job_name, cfg.window_seconds, store)
    exceeded = count >= cfg.max_pins
    msg = (
        f"pin count {count}/{cfg.max_pins} exceeded — job blocked"
        if exceeded
        else f"pin count {count}/{cfg.max_pins} within limit"
    )
    return PinCountResult(
        pinned_count=count,
        max_pins=cfg.max_pins,
        exceeded=exceeded,
        message=msg,
    )

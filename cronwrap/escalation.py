"""Escalation policy: notify additional channels after repeated failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import HistoryStore


@dataclass
class EscalationConfig:
    """Configuration for failure escalation."""

    enabled: bool = True
    # Number of consecutive failures before escalating
    threshold: int = 3
    # Channels to notify on escalation (arbitrary strings, handled externally)
    channels: List[str] = field(default_factory=list)
    # Optional cooldown in seconds between repeated escalations (0 = always)
    cooldown_seconds: int = 0

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")


def escalation_from_dict(data: dict) -> EscalationConfig:
    return EscalationConfig(
        enabled=data.get("enabled", True),
        threshold=data.get("threshold", 3),
        channels=list(data.get("channels", [])),
        cooldown_seconds=data.get("cooldown_seconds", 0),
    )


@dataclass
class EscalationResult:
    should_escalate: bool
    consecutive_failures: int
    channels: List[str]
    reason: str

    def summary(self) -> str:
        if not self.should_escalate:
            return f"No escalation ({self.reason})"
        return (
            f"Escalating after {self.consecutive_failures} consecutive failures "
            f"to {len(self.channels)} channel(s): {', '.join(self.channels)}"
        )


def count_consecutive_failures(job_name: str, store: HistoryStore) -> int:
    """Return the number of trailing consecutive failures for a job."""
    entries = store.for_job(job_name)
    count = 0
    for entry in reversed(entries):
        if entry.succeeded():
            break
        count += 1
    return count


def check_escalation(
    job_name: str,
    cfg: EscalationConfig,
    store: HistoryStore,
    last_escalation_ts: Optional[float] = None,
    now_ts: Optional[float] = None,
) -> EscalationResult:
    """Determine whether escalation should fire."""
    import time

    if not cfg.enabled:
        return EscalationResult(False, 0, [], "escalation disabled")

    consecutive = count_consecutive_failures(job_name, store)

    if consecutive < cfg.threshold:
        return EscalationResult(
            False, consecutive, [], f"{consecutive} failures < threshold {cfg.threshold}"
        )

    if cfg.cooldown_seconds > 0 and last_escalation_ts is not None:
        now = now_ts if now_ts is not None else time.time()
        elapsed = now - last_escalation_ts
        if elapsed < cfg.cooldown_seconds:
            remaining = cfg.cooldown_seconds - elapsed
            return EscalationResult(
                False, consecutive, [], f"cooldown active ({remaining:.0f}s remaining)"
            )

    return EscalationResult(True, consecutive, list(cfg.channels), "threshold reached")

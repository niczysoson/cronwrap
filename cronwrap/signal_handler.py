"""Graceful shutdown via OS signals for cron jobs."""

import signal
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


@dataclass
class SignalHandlerConfig:
    signals: List[int] = field(default_factory=lambda: [signal.SIGTERM, signal.SIGINT])
    on_signal: Optional[Callable[[int], None]] = None

    def __post_init__(self):
        if not self.signals:
            raise ValueError("signals list must not be empty")


_triggered: List[int] = []
_callbacks: List[Callable[[int], None]] = []


def _handler(signum: int, _frame) -> None:
    log.warning("Signal %d received — requesting graceful shutdown", signum)
    _triggered.append(signum)
    for cb in _callbacks:
        try:
            cb(signum)
        except Exception as exc:  # noqa: BLE001
            log.error("Signal callback raised: %s", exc)


def register(config: SignalHandlerConfig) -> None:
    """Install signal handlers defined in *config*."""
    _triggered.clear()
    _callbacks.clear()
    if config.on_signal is not None:
        _callbacks.append(config.on_signal)
    for sig in config.signals:
        signal.signal(sig, _handler)
    log.debug("Registered handlers for signals: %s", config.signals)


def was_signalled() -> bool:
    """Return True if any registered signal has fired."""
    return bool(_triggered)


def last_signal() -> Optional[int]:
    """Return the most recently received signal number, or None."""
    return _triggered[-1] if _triggered else None


def reset() -> None:
    """Clear state and restore default handlers (useful in tests)."""
    _triggered.clear()
    _callbacks.clear()

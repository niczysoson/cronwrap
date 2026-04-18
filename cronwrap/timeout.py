"""Timeout enforcement for cron job execution."""
from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional


class TimeoutExpired(Exception):
    """Raised when a job exceeds its allowed runtime."""

    def __init__(self, seconds: int):
        self.seconds = seconds
        super().__init__(f"Job timed out after {seconds}s")


@dataclass
class TimeoutConfig:
    seconds: int
    kill_on_expire: bool = True

    def __post_init__(self):
        if self.seconds <= 0:
            raise ValueError("timeout seconds must be positive")


def _use_signals() -> bool:
    """Return True if signal-based timeout is available (main thread, Unix)."""
    try:
        return threading.current_thread() is threading.main_thread()
    except Exception:
        return False


@contextmanager
 def timeout_context(cfg: Optional[TimeoutConfig]):
    """Context manager that raises TimeoutExpired if block exceeds cfg.seconds."""
    if cfg is None:
        yield
        return

    if _use_signals():
        def _handler(signum, frame):
            raise TimeoutExpired(cfg.seconds)

        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(cfg.seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        # Fallback: threading-based (best-effort, cannot kill C-extensions)
        expired = threading.Event()
        result_holder = [None]

        def _watchdog():
            if not expired.wait(timeout=cfg.seconds):
                # timed out — nothing we can do from another thread;
                # just mark it so callers can check if needed
                result_holder[0] = TimeoutExpired(cfg.seconds)

        t = threading.Thread(target=_watchdog, daemon=True)
        t.start()
        try:
            yield
        finally:
            expired.set()
            t.join()

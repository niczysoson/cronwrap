"""CLI helpers for throttle status reporting."""
from __future__ import annotations

import time
from pathlib import Path
from typing import List

from cronwrap.throttle import ThrottleConfig, is_throttled, last_success_time
from cronwrap.history import JobHistory


def _fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"


def render_throttle_status(
    job_names: List[str],
    cfg: ThrottleConfig,
    history: JobHistory,
) -> str:
    """Return a human-readable throttle status table."""
    lines = [
        f"Throttle interval: {cfg.min_interval_seconds}s",
        f"{'Job':<30} {'Last Success':<20} {'Throttled'}",
        "-" * 60,
    ]
    now = time.time()
    for name in job_names:
        last = last_success_time(name, history)
        if last is None:
            last_str = "never"
        else:
            last_str = f"{_fmt_elapsed(now - last)} ago"
        throttled = is_throttled(name, cfg, history)
        symbol = "YES" if throttled else "no"
        lines.append(f"{name:<30} {last_str:<20} {symbol}")
    return "\n".join(lines)


def check_and_exit_if_throttled(
    job_name: str,
    cfg: ThrottleConfig | None,
    history: JobHistory,
) -> bool:
    """Return True (and print a message) if the job should be skipped."""
    if cfg is None:
        return False
    if is_throttled(job_name, cfg, history):
        last = last_success_time(job_name, history)
        elapsed = time.time() - last  # type: ignore[operator]
        remaining = cfg.min_interval_seconds - elapsed
        print(
            f"[cronwrap] Skipping '{job_name}': throttled. "
            f"Next run allowed in {_fmt_elapsed(remaining)}."
        )
        return True
    return False

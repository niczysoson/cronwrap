"""CLI helpers for notify-window status rendering."""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

from .notifywindow import NotifyWindowConfig, NotifyWindowResult, is_notify_allowed


def _symbol(allowed: bool) -> str:
    return "\u2705" if allowed else "\u274c"


def render_notify_window_config(cfg: NotifyWindowConfig) -> str:
    lines = ["Notify Window Configuration:"]
    lines.append(f"  enabled  : {cfg.enabled}")
    lines.append(f"  timezone : {cfg.timezone}")
    if cfg.windows:
        lines.append("  windows  :")
        for w in cfg.windows:
            lines.append(f"    - {w}")
    else:
        lines.append("  windows  : (none — always allowed)")
    return "\n".join(lines)


def render_notify_window_result(result: NotifyWindowResult) -> str:
    sym = _symbol(result.allowed)
    return f"{sym} {result.summary()}"


def check_and_exit_if_suppressed(
    cfg: NotifyWindowConfig,
    now: Optional[datetime] = None,
    *,
    exit_code: int = 0,
) -> None:
    """Print status and exit with *exit_code* if notifications are suppressed."""
    result = is_notify_allowed(cfg, now=now)
    print(render_notify_window_result(result))
    if not result.allowed:
        sys.exit(exit_code)

"""CLI helpers for blackout window status."""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

from cronwrap.blackout import BlackoutConfig


def render_blackout_status(cfg: BlackoutConfig, now: Optional[datetime] = None) -> str:
    """Return a human-readable summary of the blackout configuration."""
    if not cfg.enabled:
        return "Blackout: disabled"
    if not cfg.windows:
        return "Blackout: enabled — no windows defined"
    if now is None:
        now = datetime.utcnow()
    blacked = cfg.is_blacked_out(now)
    symbol = "\u23d0" if blacked else "\u25cb"  # ⏐ blocked  ○ clear
    lines = [f"Blackout: {symbol} {'BLOCKED' if blacked else 'clear'} at {now.strftime('%H:%M')} UTC"]
    for w in cfg.windows:
        lines.append(f"  window: {w}")
    return "\n".join(lines)


def check_and_exit_if_blacked_out(
    cfg: BlackoutConfig,
    now: Optional[datetime] = None,
    exit_code: int = 0,
) -> None:
    """Print status and exit with *exit_code* when inside a blackout window."""
    if cfg.is_blacked_out(now):
        print(render_blackout_status(cfg, now))
        sys.exit(exit_code)

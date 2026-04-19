"""CLI helpers for heartbeat status."""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from cronwrap.heartbeat import HeartbeatConfig, is_stale, read_beat


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


def render_heartbeat_status(cfg: HeartbeatConfig) -> str:
    last = read_beat(cfg)
    lines: list[str] = [f"Heartbeat: {cfg.job_name}"]
    if last is None:
        lines.append("  Last beat : never")
        lines.append("  Status    : MISSING")
        return "\n".join(lines)

    age = (datetime.now(timezone.utc) - last).total_seconds()
    stale = is_stale(cfg)
    symbol = "\u26a0\ufe0f  STALE" if stale else "\u2705 OK"
    lines.append(f"  Last beat : {last.isoformat()}")
    lines.append(f"  Age       : {_fmt_age(age)}")
    if cfg.max_age_seconds is not None:
        lines.append(f"  Max age   : {_fmt_age(cfg.max_age_seconds)}")
    lines.append(f"  Status    : {symbol}")
    return "\n".join(lines)


def check_and_exit_if_stale(cfg: HeartbeatConfig) -> None:
    """Print status and exit with code 1 if the heartbeat is stale."""
    print(render_heartbeat_status(cfg))
    if is_stale(cfg):
        sys.exit(1)

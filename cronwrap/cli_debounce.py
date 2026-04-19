"""CLI helpers for debounce status rendering."""
from __future__ import annotations

import sys

from cronwrap.debounce import DebounceConfig, elapsed_seconds, is_debounced
from cronwrap.history import JobHistory


def _fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    m = int(s) // 60
    sec = int(s) % 60
    return f"{m}m {sec}s"


def render_debounce_status(cfg: DebounceConfig, history: JobHistory) -> str:
    lines = [
        f"Debounce config for job: {cfg.job_name}",
        f"  Cooldown : {_fmt_seconds(cfg.cooldown_seconds)}",
    ]
    elapsed = elapsed_seconds(cfg, history)
    if elapsed is None:
        lines.append("  Last run : never")
        lines.append("  Status   : ✓ not debounced (no history)")
    else:
        lines.append(f"  Last run : {_fmt_seconds(elapsed)} ago")
        remaining = cfg.cooldown_seconds - elapsed
        if remaining > 0:
            lines.append(f"  Status   : ✗ debounced ({_fmt_seconds(remaining)} remaining)")
        else:
            lines.append("  Status   : ✓ not debounced")
    return "\n".join(lines)


def check_and_exit_if_debounced(
    cfg: DebounceConfig, history: JobHistory, *, verbose: bool = False
) -> None:
    """Print status and exit(0) (skip) if job is within cooldown window."""
    if is_debounced(cfg, history):
        if verbose:
            print(render_debounce_status(cfg, history))
        else:
            elapsed = elapsed_seconds(cfg, history) or 0
            remaining = cfg.cooldown_seconds - elapsed
            print(
                f"[debounce] Skipping '{cfg.job_name}': "
                f"cooldown active, {_fmt_seconds(remaining)} remaining."
            )
        sys.exit(0)

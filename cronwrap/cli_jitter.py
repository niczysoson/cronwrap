"""CLI helpers for jitter status and dry-run preview."""
from __future__ import annotations
import sys
from cronwrap.jitter import JitterConfig, render_jitter


def render_jitter_status(cfg: JitterConfig) -> str:
    lines = [render_jitter(cfg)]
    if cfg.enabled and cfg.max_seconds > 0:
        sample = [round(cfg.delay(), 2) for _ in range(5)]
        lines.append(f"  sample delays (s): {sample}")
    return "\n".join(lines)


def check_and_apply_jitter(cfg: JitterConfig, *, dry_run: bool = False) -> float:
    """Apply jitter sleep unless dry_run.  Returns planned delay."""
    delay = cfg.delay()
    if dry_run:
        print(f"[jitter] would sleep {delay:.2f}s (dry-run, skipping)", file=sys.stderr)
        return delay
    if delay > 0:
        print(f"[jitter] sleeping {delay:.2f}s", file=sys.stderr)
        import time
        time.sleep(delay)
    return delay

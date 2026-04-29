"""CLI helpers for displaying and enforcing grace period status."""
from __future__ import annotations

import sys

from cronwrap.grace import GraceConfig, GraceResult, check_grace
from cronwrap.history import JobHistory


def _fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    minutes = int(s) // 60
    secs = int(s) % 60
    return f"{minutes}m {secs:02d}s"


def render_grace_status(config: GraceConfig, result: GraceResult) -> str:
    lines: list[str] = []
    status = "ACTIVE" if result.in_grace else "EXPIRED"
    symbol = "⏳" if result.in_grace else "✓"
    lines.append(f"{symbol} Grace period [{status}]")
    lines.append(f"  Window : {_fmt_seconds(config.grace_seconds)}")
    if result.first_run_at is not None:
        lines.append(f"  First run : {result.first_run_at.isoformat(timespec='seconds')}")
    if result.elapsed_seconds is not None:
        lines.append(f"  Elapsed   : {_fmt_seconds(result.elapsed_seconds)}")
        if result.in_grace:
            remaining = max(0.0, result.grace_seconds - result.elapsed_seconds)
            lines.append(f"  Remaining : {_fmt_seconds(remaining)}")
    if result.first_run_at is None and result.in_grace:
        lines.append("  (no history — first run assumed)")
    return "\n".join(lines)


def check_and_exit_if_in_grace(
    config: GraceConfig,
    history: JobHistory,
    *,
    suppress_failures: bool = True,
) -> GraceResult:
    """Check grace period; if active and suppress_failures is True, print status and exit 0."""
    result = check_grace(config, history)
    if result.in_grace and suppress_failures:
        print(render_grace_status(config, result))
        sys.exit(0)
    return result

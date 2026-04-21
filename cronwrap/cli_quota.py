"""CLI helpers for quota status display and enforcement."""
from __future__ import annotations

import sys

from cronwrap.quota import QuotaConfig, HistoryStore, quota_status, is_quota_exceeded


def _fmt_window(seconds: int) -> str:
    """Format a duration in seconds as a human-readable string (e.g. '30s', '5m', '2h')."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h"


def render_quota_status(cfg: QuotaConfig, store: HistoryStore) -> str:
    """Return a formatted multi-line string summarising the current quota status."""
    s = quota_status(cfg, store)
    symbol = "\u274c" if s["exceeded"] else "\u2705"
    window = _fmt_window(s["window_seconds"])
    lines = [
        f"Quota status for '{s['job_name'] or '(all)'}'" ,
        f"  Window  : {window}",
        f"  Max runs: {s['max_runs']}",
        f"  Used    : {s['runs_in_window']}",
        f"  Left    : {s['remaining']}",
        f"  Status  : {symbol} {'EXCEEDED' if s['exceeded'] else 'OK'}",
    ]
    return "\n".join(lines)


def check_and_exit_if_quota_exceeded(cfg: QuotaConfig, store: HistoryStore) -> None:
    """Print quota status and exit with code 1 if quota is exceeded."""
    print(render_quota_status(cfg, store))
    if is_quota_exceeded(cfg, store):
        print("[cronwrap] quota exceeded – skipping job", file=sys.stderr)
        sys.exit(1)


def print_quota_status(cfg: QuotaConfig, store: HistoryStore, *, file=None) -> None:
    """Print the quota status summary to *file* (defaults to stdout).

    Unlike :func:`check_and_exit_if_quota_exceeded`, this function never
    terminates the process – it is intended for informational display only.
    """
    if file is None:
        file = sys.stdout
    print(render_quota_status(cfg, store), file=file)

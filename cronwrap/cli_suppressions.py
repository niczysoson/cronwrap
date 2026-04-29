"""CLI rendering helpers for suppression rules."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from cronwrap.suppressions import SuppressionRule, SuppressionStore


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _fmt_remaining(expires_at: datetime, now: datetime) -> str:
    delta = expires_at - now
    total = int(delta.total_seconds())
    if total <= 0:
        return "expired"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def render_suppression_list(rules: List[SuppressionRule], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if not rules:
        return "No active suppressions."
    lines = [f"{'JOB':<24} {'EXPIRES':<20} {'REMAINING':<12} REASON"]
    lines.append("-" * 72)
    for r in rules:
        remaining = _fmt_remaining(r.expires_at, now)
        lines.append(f"{r.job_name:<24} {_fmt_dt(r.expires_at):<20} {remaining:<12} {r.reason}")
    return "\n".join(lines)


def check_and_exit_if_suppressed(
    store: SuppressionStore,
    job_name: str,
    now: datetime | None = None,
) -> None:
    """Print a warning and raise SystemExit(0) if the job is currently suppressed."""
    if not store.is_suppressed(job_name, now):
        return
    rules = store.active_for_job(job_name, now)
    reason = rules[0].reason if rules else "suppressed"
    print(f"[suppressed] {job_name}: {reason}")
    raise SystemExit(0)

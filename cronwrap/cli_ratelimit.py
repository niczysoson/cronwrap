"""CLI helpers for displaying rate-limit status."""
from __future__ import annotations

from cronwrap.ratelimit import RateLimitConfig, rate_limit_status
from cronwrap.history import HistoryStore


def _fmt_window(seconds: int) -> str:
    if seconds < 120:
        return f"{seconds}s"
    if seconds < 7200:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h"


def render_rate_limit_status(job_name: str, config: RateLimitConfig, store: HistoryStore) -> str:
    s = rate_limit_status(job_name, config, store)
    symbol = "\u274c" if s["limited"] else "\u2705"
    window = _fmt_window(s["window_seconds"])
    lines = [
        f"{symbol} Rate limit: {job_name}",
        f"   runs in window : {s['recent_runs']} / {s['max_runs']}",
        f"   window         : {window}",
        f"   limited        : {s['limited']}",
    ]
    return "\n".join(lines)


def check_and_exit_if_rate_limited(
    job_name: str,
    config: RateLimitConfig,
    store: HistoryStore,
) -> None:
    """Print status and raise SystemExit(2) if rate-limited."""
    from cronwrap.ratelimit import is_rate_limited

    print(render_rate_limit_status(job_name, config, store))
    if is_rate_limited(job_name, config, store):
        raise SystemExit(2)

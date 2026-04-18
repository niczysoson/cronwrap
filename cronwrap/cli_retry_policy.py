"""CLI helpers for displaying retry policy information."""
from __future__ import annotations
from cronwrap.retry_policy import RetryPolicy


def render_retry_policy(policy: RetryPolicy) -> str:
    lines = [
        "Retry Policy",
        f"  Max attempts   : {policy.max_attempts}",
        f"  Initial delay  : {policy.delay_seconds}s",
        f"  Backoff factor : {policy.backoff_factor}x",
    ]
    if policy.retry_on_exit_codes is not None:
        codes = ", ".join(str(c) for c in policy.retry_on_exit_codes)
        lines.append(f"  Retry on codes : {codes}")
    else:
        lines.append("  Retry on codes : any non-zero")
    return "\n".join(lines)


def render_attempt_schedule(policy: RetryPolicy) -> str:
    """Show the wait time before each attempt."""
    lines = ["Attempt schedule:"]
    for i in range(policy.max_attempts):
        wait = policy.wait_seconds(i)
        if wait == 0:
            lines.append(f"  Attempt {i + 1}: immediate")
        else:
            lines.append(f"  Attempt {i + 1}: after {wait:.1f}s")
    return "\n".join(lines)

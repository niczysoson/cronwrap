"""CLI helpers for sticky failure state."""
from __future__ import annotations

from cronwrap.sticky import StickyConfig


def render_sticky_status(cfg: StickyConfig, job_name: str) -> str:
    """Return a human-readable status line for a job's sticky state."""
    if not cfg.enabled:
        return f"[sticky] disabled for '{job_name}'"

    st = cfg.state(job_name)
    if st is None:
        return f"[sticky] '{job_name}' — no active failure"

    failed_at = st.get("failed_at", "unknown")
    exit_code = st.get("exit_code", "?")
    return (
        f"[sticky] '{job_name}' — STUCK since {failed_at} "
        f"(exit_code={exit_code})"
    )


def check_and_exit_if_sticky(cfg: StickyConfig, job_name: str) -> None:
    """Print status and raise SystemExit(1) if the job is currently sticky.

    Intended for use in CLI entry points that want to block re-runs while
    a job is in a known-failed state.
    """
    print(render_sticky_status(cfg, job_name))
    if cfg.is_sticky(job_name):
        raise SystemExit(1)

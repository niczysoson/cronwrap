"""CLI helpers for manual trigger status and control."""
from __future__ import annotations

from cronwrap.trigger import TriggerConfig


def _symbol(triggered: bool) -> str:
    return "\u26a1" if triggered else "\u2014"


def render_trigger_status(cfg: TriggerConfig, job_name: str) -> str:
    """Return a human-readable status string for a job's trigger state."""
    if not cfg.enabled:
        return "triggers: disabled"
    triggered = cfg.is_triggered(job_name)
    symbol = _symbol(triggered)
    if triggered:
        info = cfg.trigger_info(job_name)
        when = info.get("triggered_at", "unknown") if info else "unknown"
        return f"{symbol} trigger pending for '{job_name}' (set at {when})"
    return f"{symbol} no pending trigger for '{job_name}'"


def check_and_exit_if_not_triggered(
    cfg: TriggerConfig,
    job_name: str,
    require_trigger: bool,
) -> None:
    """If *require_trigger* is True and no trigger is set, raise SystemExit(0).

    Call ``cfg.clear_trigger`` after a successful run to consume the trigger.
    """
    if not require_trigger:
        return
    if not cfg.is_triggered(job_name):
        print(f"[cronwrap] no manual trigger set for '{job_name}' — skipping.")
        raise SystemExit(0)

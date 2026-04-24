"""CLI rendering helpers for escalation status."""
from __future__ import annotations

from cronwrap.escalation import EscalationConfig, EscalationResult, check_escalation
from cronwrap.history import HistoryStore


def render_escalation_config(cfg: EscalationConfig) -> str:
    lines = ["Escalation Policy:"]
    lines.append(f"  Enabled   : {'yes' if cfg.enabled else 'no'}")
    lines.append(f"  Threshold : {cfg.threshold} consecutive failure(s)")
    lines.append(f"  Channels  : {', '.join(cfg.channels) if cfg.channels else '(none)'}")
    if cfg.cooldown_seconds:
        lines.append(f"  Cooldown  : {cfg.cooldown_seconds}s between escalations")
    else:
        lines.append("  Cooldown  : none")
    return "\n".join(lines)


def render_escalation_result(result: EscalationResult) -> str:
    symbol = "🔺" if result.should_escalate else "✓"
    lines = [f"{symbol} {result.summary()}"]
    if result.should_escalate and result.channels:
        lines.append("  Notify channels:")
        for ch in result.channels:
            lines.append(f"    - {ch}")
    return "\n".join(lines)


def check_and_exit_if_escalating(
    job_name: str,
    cfg: EscalationConfig,
    store: HistoryStore,
    last_escalation_ts: float | None = None,
) -> EscalationResult:
    """Check escalation status, print result, and return it.

    Callers are responsible for actually dispatching to channels.
    """
    result = check_escalation(job_name, cfg, store, last_escalation_ts)
    print(render_escalation_result(result))
    return result

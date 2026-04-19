"""CLI helpers for alert manager status display."""
from __future__ import annotations
from typing import List
from cronwrap.alertmanager import AlertManagerConfig, AlertRule


def _rule_line(rule: AlertRule) -> str:
    status = "on " if rule.enabled else "off"
    events = ",".join(rule.events)
    return f"  [{status}] channel={rule.channel} events={events} min_exit={rule.min_exit_code}"


def render_alert_rules(config: AlertManagerConfig) -> str:
    if not config.rules:
        return "alert-manager: no rules configured"
    lines = ["alert-manager rules:"]
    for rule in config.rules:
        lines.append(_rule_line(rule))
    return "\n".join(lines)


def render_dispatch_result(channels: List[str]) -> str:
    if not channels:
        return "alert-manager: no channels notified"
    joined = ", ".join(channels)
    return f"alert-manager: notified channels: {joined}"

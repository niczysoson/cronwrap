"""CLI helpers for displaying the audit log."""
from __future__ import annotations

from typing import List, Optional

from .audit import AuditEvent, AuditLog

_SYMBOLS = {
    "started": "▶",
    "succeeded": "✔",
    "failed": "✘",
    "retry": "↺",
    "throttled": "⏸",
    "locked": "🔒",
}


def _symbol(event: str) -> str:
    return _SYMBOLS.get(event, "?")


def render_audit_events(events: List[AuditEvent], limit: Optional[int] = None) -> str:
    if not events:
        return "No audit events found."
    shown = events[-limit:] if limit else events
    lines = []
    for e in shown:
        sym = _symbol(e.event)
        detail = f"  ({e.detail})" if e.detail else ""
        code = f"  exit={e.exit_code}" if e.exit_code is not None else ""
        lines.append(f"{e.timestamp}  {sym} [{e.event:<10}]  {e.job_name}{code}{detail}")
    return "\n".join(lines)


def print_audit(log: AuditLog, job_name: Optional[str] = None,
                event_filter: Optional[str] = None, limit: int = 50) -> None:
    events = log.filter(job_name=job_name, event=event_filter)
    print(render_audit_events(events, limit=limit))

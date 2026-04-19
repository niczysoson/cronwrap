"""CLI rendering for tracing spans."""
from __future__ import annotations

from typing import List

from cronwrap.tracing import Span


def _status_symbol(status: str) -> str:
    return {"ok": "✓", "error": "✗", "running": "…"}.get(status, "?")


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "(running)"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.2f}s"


def render_spans(spans: List[Span]) -> str:
    if not spans:
        return "No spans recorded."
    lines = []
    for s in spans:
        sym = _status_symbol(s.status)
        dur = _fmt_duration(s.duration_seconds)
        lines.append(f"  {sym} [{s.span_id}] {s.name}  {dur}  ({s.status})")
    return "\n".join(lines)


def render_trace(trace_id: str, spans: List[Span]) -> str:
    header = f"Trace {trace_id}  ({len(spans)} span(s))"
    body = render_spans(spans)
    return f"{header}\n{body}"


def render_job_traces(job_name: str, spans: List[Span]) -> str:
    if not spans:
        return f"No traces for job '{job_name}'."
    # group by trace_id preserving order
    seen: dict = {}
    for s in spans:
        seen.setdefault(s.trace_id, []).append(s)
    blocks = []
    for tid, group in seen.items():
        blocks.append(render_trace(tid, group))
    return f"Job: {job_name}\n" + "\n\n".join(blocks)

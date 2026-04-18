"""Simple text-based dashboard for viewing job history and status."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from cronwrap.history import JobHistory, HistoryEntry


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def _status_symbol(success: bool) -> str:
    return "✓" if success else "✗"


def render_job_summary(history: JobHistory, job_name: str, limit: int = 10) -> str:
    entries: List[HistoryEntry] = history.get(job_name, limit=limit)
    if not entries:
        return f"No history found for job: {job_name}\n"

    lines = [f"Job: {job_name}", "-" * 50]
    total = len(entries)
    successes = sum(1 for e in entries if e.success)
    lines.append(f"Last {total} runs: {successes}/{total} succeeded")
    lines.append("")
    lines.append(f"{'Time':<22} {'Status':<8} {'Duration':<12} {'Exit Code'}")
    lines.append("-" * 50)
    for entry in entries:
        ts = entry.started_at.strftime("%Y-%m-%d %H:%M:%S")
        symbol = _status_symbol(entry.success)
        duration = _format_duration(entry.duration_seconds)
        lines.append(f"{ts:<22} {symbol:<8} {duration:<12} {entry.exit_code}")
    return "\n".join(lines) + "\n"


def render_all_jobs(history: JobHistory) -> str:
    job_names = history.list_jobs()
    if not job_names:
        return "No job history available.\n"

    lines = ["All Jobs Summary", "=" * 50]
    lines.append(f"{'Job':<30} {'Runs':<6} {'Success Rate':<14} {'Last Run'}")
    lines.append("-" * 50)
    for name in sorted(job_names):
        entries = history.get(name, limit=50)
        total = len(entries)
        successes = sum(1 for e in entries if e.success)
        rate = f"{100 * successes // total}%" if total else "N/A"
        last = entries[0].started_at.strftime("%Y-%m-%d %H:%M") if entries else "never"
        lines.append(f"{name:<30} {total:<6} {rate:<14} {last}")
    return "\n".join(lines) + "\n"

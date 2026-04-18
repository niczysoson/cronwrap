"""Export metrics to JSON or plain-text formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from cronwrap.metrics import JobMetrics


def to_json(metrics: List[JobMetrics], indent: int = 2) -> str:
    """Serialize a list of JobMetrics to a JSON string."""
    return json.dumps([m.to_dict() for m in metrics], indent=indent)


def to_text(metrics: List[JobMetrics]) -> str:
    """Render metrics as a human-readable text table."""
    if not metrics:
        return "No metrics available."

    header = f"{'Job':<30} {'Runs':>6} {'OK':>6} {'Fail':>6} {'Rate':>7} {'Avg(s)':>8} {'Min(s)':>8} {'Max(s)':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for m in metrics:
        rate = f"{m.success_rate * 100:.1f}%"
        avg = f"{m.avg_duration_seconds:.2f}" if m.total_runs else "—"
        lo = f"{m.min_duration_seconds:.2f}" if m.min_duration_seconds is not None else "—"
        hi = f"{m.max_duration_seconds:.2f}" if m.max_duration_seconds is not None else "—"
        lines.append(
            f"{m.job_name:<30} {m.total_runs:>6} {m.successful_runs:>6} "
            f"{m.failed_runs:>6} {rate:>7} {avg:>8} {lo:>8} {hi:>8}"
        )
    return "\n".join(lines)


def write_json(metrics: List[JobMetrics], path: Path) -> None:
    """Write metrics as JSON to *path*."""
    path.write_text(to_json(metrics))


def write_text(metrics: List[JobMetrics], path: Path) -> None:
    """Write metrics as plain text to *path*."""
    path.write_text(to_text(metrics))

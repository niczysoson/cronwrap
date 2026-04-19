"""CLI rendering for job step progress."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwrap.progress import JobProgress, load_progress

_SYMBOLS = {"pending": "○", "running": "◎", "done": "✓", "failed": "✗"}


def _fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds // 60)}m {int(seconds % 60)}s"


def render_progress(progress: JobProgress) -> str:
    lines = [f"Progress: {progress.job_name}"]
    lines.append("-" * 40)
    for step in progress.steps:
        sym = _SYMBOLS.get(step.status, "?")
        dur = _fmt_duration(step.duration_seconds)
        msg = f"  {step.message}" if step.message else ""
        lines.append(f"  {sym} {step.name:<24} [{dur}]{msg}")
    total = len(progress.steps)
    done = sum(1 for s in progress.steps if s.status == "done")
    failed = sum(1 for s in progress.steps if s.status == "failed")
    lines.append("-" * 40)
    lines.append(f"  {done}/{total} done, {failed} failed")
    return "\n".join(lines)


def print_progress(path: Path) -> int:
    """Load and print progress from file. Returns 1 if not found."""
    progress = load_progress(path)
    if progress is None:
        print(f"No progress file found at {path}")
        return 1
    print(render_progress(progress))
    return 0

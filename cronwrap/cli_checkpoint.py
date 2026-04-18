"""CLI helpers for inspecting and managing checkpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwrap.checkpoint import Checkpoint, load_checkpoint, clear_checkpoint, _DEFAULT_DIR


def render_checkpoint(job_name: str, directory: Path = _DEFAULT_DIR) -> str:
    cp = load_checkpoint(job_name, directory)
    if cp is None:
        return f"No checkpoint found for job '{job_name}'."
    lines = [f"Checkpoint: {job_name}"]
    if not cp.completed_steps:
        lines.append("  Completed steps: (none)")
    else:
        lines.append("  Completed steps:")
        for step in cp.completed_steps:
            lines.append(f"    ✓ {step}")
    if cp.metadata:
        lines.append("  Metadata:")
        for k, v in cp.metadata.items():
            lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def print_checkpoint(job_name: str, directory: Path = _DEFAULT_DIR) -> None:
    print(render_checkpoint(job_name, directory))


def cmd_clear_checkpoint(job_name: str, directory: Path = _DEFAULT_DIR) -> None:
    removed = clear_checkpoint(job_name, directory)
    if removed:
        print(f"Checkpoint cleared for job '{job_name}'.")
    else:
        print(f"No checkpoint to clear for job '{job_name}'.")

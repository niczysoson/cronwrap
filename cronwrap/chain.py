"""Job chaining: run a sequence of commands, stopping on first failure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.runner import RunResult, run


@dataclass
class ChainResult:
    job_name: str
    steps: List[RunResult] = field(default_factory=list)
    stopped_at: Optional[int] = None  # index of failing step

    @property
    def succeeded(self) -> bool:
        return self.stopped_at is None

    @property
    def failed_step(self) -> Optional[RunResult]:
        if self.stopped_at is not None:
            return self.steps[self.stopped_at]
        return None


def run_chain(
    job_name: str,
    commands: List[str],
    timeout: Optional[int] = None,
    stop_on_failure: bool = True,
) -> ChainResult:
    """Execute a list of commands in order.

    Args:
        job_name: Logical name for the chain.
        commands: Shell commands to run in sequence.
        timeout: Per-step timeout in seconds (passed to runner).
        stop_on_failure: If True, abort remaining steps on first non-zero exit.

    Returns:
        ChainResult summarising all executed steps.
    """
    result = ChainResult(job_name=job_name)
    for idx, cmd in enumerate(commands):
        step = run(cmd, timeout=timeout)
        result.steps.append(step)
        if stop_on_failure and not step.succeeded:
            result.stopped_at = idx
            break
    return result


def chain_from_dict(data: dict) -> ChainResult:
    """Re-hydrate a ChainResult from a plain dict (e.g. loaded from JSON)."""
    steps = []
    for s in data.get("steps", []):
        steps.append(
            RunResult(
                command=s["command"],
                returncode=s["returncode"],
                stdout=s.get("stdout", ""),
                stderr=s.get("stderr", ""),
                duration=s.get("duration", 0.0),
            )
        )
    cr = ChainResult(job_name=data["job_name"], steps=steps)
    cr.stopped_at = data.get("stopped_at")
    return cr

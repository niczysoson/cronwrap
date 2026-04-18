"""Route job output to different destinations (file, stderr, null)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional
from cronwrap.runner import RunResult


@dataclass
class OutputRoute:
    stdout_file: Optional[str] = None
    stderr_file: Optional[str] = None
    suppress_stdout: bool = False
    suppress_stderr: bool = False
    append: bool = False

    def __post_init__(self) -> None:
        if self.stdout_file and self.suppress_stdout:
            raise ValueError("Cannot both write stdout to file and suppress it")
        if self.stderr_file and self.suppress_stderr:
            raise ValueError("Cannot both write stderr to file and suppress it")


def route_from_dict(d: dict) -> OutputRoute:
    return OutputRoute(
        stdout_file=d.get("stdout_file"),
        stderr_file=d.get("stderr_file"),
        suppress_stdout=bool(d.get("suppress_stdout", False)),
        suppress_stderr=bool(d.get("suppress_stderr", False)),
        append=bool(d.get("append", False)),
    )


def _write(path: str, text: str, append: bool) -> None:
    mode = "a" if append else "w"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, mode) as fh:
        fh.write(text)


def apply_output_route(result: RunResult, route: OutputRoute) -> RunResult:
    """Write/suppress stdout and stderr according to *route*.

    Returns a new RunResult with fields replaced when suppressed.
    """
    stdout = result.stdout
    stderr = result.stderr

    if route.stdout_file and stdout:
        _write(route.stdout_file, stdout, route.append)
    if route.suppress_stdout:
        stdout = ""

    if route.stderr_file and stderr:
        _write(route.stderr_file, stderr, route.append)
    if route.suppress_stderr:
        stderr = ""

    return RunResult(
        returncode=result.returncode,
        stdout=stdout,
        stderr=stderr,
        duration=result.duration,
    )


def render_route(route: OutputRoute) -> str:
    lines = ["Output routing:"]
    lines.append(f"  stdout -> {'(suppressed)' if route.suppress_stdout else route.stdout_file or '(passthrough)'}")
    lines.append(f"  stderr -> {'(suppressed)' if route.suppress_stderr else route.stderr_file or '(passthrough)'}")
    lines.append(f"  append mode: {route.append}")
    return "\n".join(lines)

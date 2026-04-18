"""Convenience integration: redact RunResult fields using MaskConfig."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from cronwrap.secrets import MaskConfig, mask_output, mask_command

if TYPE_CHECKING:
    from cronwrap.runner import RunResult


def redact_result(result: "RunResult", cfg: Optional[MaskConfig]) -> "RunResult":
    """Return a new RunResult with sensitive data replaced."""
    if cfg is None:
        return result
    from cronwrap.runner import RunResult
    return RunResult(
        command=mask_command(result.command, cfg),
        returncode=result.returncode,
        stdout=mask_output(result.stdout, cfg),
        stderr=mask_output(result.stderr, cfg),
        duration=result.duration,
        attempts=result.attempts,
    )


def redact_dict(d: dict, cfg: Optional[MaskConfig]) -> dict:
    """Recursively mask string values in a dict."""
    if cfg is None:
        return d
    from cronwrap.secrets import mask_text
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = mask_text(v, cfg)
        elif isinstance(v, dict):
            out[k] = redact_dict(v, cfg)
        else:
            out[k] = v
    return out

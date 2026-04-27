"""CLI helpers for host fencing."""
from __future__ import annotations

import sys

from cronwrap.fencing import FenceConfig, FenceResult, check_fence


def render_fence_config(config: FenceConfig) -> str:
    """Return a human-readable summary of the fence configuration."""
    if not config.enabled:
        return "Fencing: disabled"
    if not config.allowed_hosts:
        return "Fencing: enabled — no host restrictions (all hosts allowed)"
    hosts = ", ".join(config.allowed_hosts)
    return f"Fencing: enabled — allowed hosts: [{hosts}]"


def render_fence_result(result: FenceResult) -> str:
    """Return a one-line status string for a FenceResult."""
    symbol = "✓" if result.allowed else "✗"
    return f"[{symbol}] {result.summary()}"


def check_and_exit_if_fenced(
    config: FenceConfig,
    hostname: str | None = None,
    *,
    verbose: bool = False,
) -> FenceResult:
    """Check fencing and exit with code 1 if the current host is not allowed.

    Returns the FenceResult when the host is permitted.
    """
    result = check_fence(config, hostname=hostname)
    if verbose:
        print(render_fence_result(result))
    if not result.allowed:
        print(render_fence_result(result), file=sys.stderr)
        sys.exit(1)
    return result

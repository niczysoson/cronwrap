"""CLI helpers for displaying and applying job isolation config."""
from __future__ import annotations

from typing import List

from .isolation import IsolationConfig


def render_isolation_config(cfg: IsolationConfig) -> List[str]:
    """Return a list of human-readable lines describing the isolation config."""
    lines: List[str] = []
    status = "enabled" if cfg.enabled else "disabled"
    lines.append(f"Isolation : {status}")

    if not cfg.enabled:
        return lines

    if cfg.allowlist:
        lines.append(f"  Allowlist ({len(cfg.allowlist)}): {', '.join(sorted(cfg.allowlist))}")
    else:
        lines.append("  Allowlist : (all variables passed through)")

    if cfg.denylist:
        lines.append(f"  Denylist  ({len(cfg.denylist)}): {', '.join(sorted(cfg.denylist))}")
    else:
        lines.append("  Denylist  : (none)")

    if cfg.inject:
        pairs = ", ".join(f"{k}={v}" for k, v in sorted(cfg.inject.items()))
        lines.append(f"  Injected  ({len(cfg.inject)}): {pairs}")
    else:
        lines.append("  Injected  : (none)")

    return lines


def summarise_env(env: dict) -> str:
    """Return a one-line summary of an environment dict."""
    return f"{len(env)} variable(s): {', '.join(sorted(env)[:5])}{'...' if len(env) > 5 else ''}"

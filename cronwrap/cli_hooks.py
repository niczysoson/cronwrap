"""CLI rendering for hook configuration and results."""
from __future__ import annotations
from typing import List
from cronwrap.hooks import HookConfig, HookResult


def render_hook_config(cfg: HookConfig) -> str:
    lines = ["Hook Configuration:",
             f"  timeout : {cfg.timeout_seconds}s",
             f"  stop on pre failure: {cfg.stop_on_pre_failure}"]
    if cfg.pre:
        lines.append("  pre hooks:")
        for c in cfg.pre:
            lines.append(f"    - {c}")
    else:
        lines.append("  pre hooks : (none)")
    if cfg.post:
        lines.append("  post hooks:")
        for c in cfg.post:
            lines.append(f"    - {c}")
    else:
        lines.append("  post hooks: (none)")
    if cfg.post_failure:
        lines.append("  post_failure hooks:")
        for c in cfg.post_failure:
            lines.append(f"    - {c}")
    return "\n".join(lines)


def render_hook_results(results: List[HookResult]) -> str:
    if not results:
        return "  (no hooks ran)"
    lines = []
    for r in results:
        sym = "✓" if r.succeeded else "✗"
        lines.append(f"  {sym} [{r.returncode}] {r.command}")
        if r.stderr.strip():
            lines.append(f"      stderr: {r.stderr.strip()[:120]}")
    return "\n".join(lines)

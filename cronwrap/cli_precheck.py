"""CLI rendering for pre-flight check results."""
from __future__ import annotations

import sys

from cronwrap.precheck import PrecheckConfig, PrecheckResult, run_prechecks


def render_precheck_status(cfg: PrecheckConfig, result: PrecheckResult) -> str:
    lines = ["Pre-flight Checks"]
    lines.append(f"  Commands : {', '.join(cfg.required_commands) or '(none)'}")
    lines.append(f"  Env vars : {', '.join(cfg.required_env) or '(none)'}")
    if cfg.min_disk_mb is not None:
        lines.append(f"  Disk     : >= {cfg.min_disk_mb} MB")
    lines.append("")
    if result.passed:
        lines.append("  ✓ All checks passed")
    else:
        for f in result.failures:
            lines.append(f"  ✗ {f}")
    return "\n".join(lines)


def check_and_exit_if_failed(cfg: PrecheckConfig) -> PrecheckResult:
    """Run checks and exit with code 1 if any fail."""
    result = run_prechecks(cfg)
    if not result.passed:
        print(render_precheck_status(cfg, result), file=sys.stderr)
        sys.exit(1)
    return result

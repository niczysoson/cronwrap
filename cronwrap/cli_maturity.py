"""CLI rendering helpers for job maturity checks."""
from __future__ import annotations

import sys

from cronwrap.maturity import MaturityConfig, MaturityResult, check_maturity
from cronwrap.history import JobHistory


_SYMBOL_OK = "\u2714"
_SYMBOL_STALE = "\u26a0"


def _fmt_age(age_hours: float | None) -> str:
    if age_hours is None:
        return "never"
    if age_hours < 1.0:
        minutes = age_hours * 60
        return f"{minutes:.0f}m ago"
    if age_hours < 48.0:
        return f"{age_hours:.1f}h ago"
    days = age_hours / 24
    return f"{days:.1f}d ago"


def render_maturity_result(result: MaturityResult) -> str:
    symbol = _SYMBOL_STALE if result.is_mature else _SYMBOL_OK
    age_str = _fmt_age(result.age_hours)
    lines = [
        f"{symbol} Job maturity: {result.job_name}",
        f"  Threshold : {result.threshold_hours}h",
        f"  Last success: {age_str}",
        f"  Status    : {'STALE' if result.is_mature else 'OK'}",
    ]
    return "\n".join(lines)


def check_and_exit_if_stale(
    cfg: MaturityConfig,
    history: JobHistory,
    *,
    exit_code: int = 1,
) -> MaturityResult:
    """Run the maturity check; print status and exit if stale."""
    result = check_maturity(cfg, history)
    print(render_maturity_result(result))
    if result.is_mature:
        sys.exit(exit_code)
    return result

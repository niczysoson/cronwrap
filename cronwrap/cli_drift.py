"""CLI helpers for schedule drift detection."""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

from cronwrap.drift import DriftConfig, DriftResult, measure_drift


def _fmt_seconds(seconds: float) -> str:
    if abs(seconds) < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"


def render_drift_status(result: DriftResult) -> str:
    lines = [
        "Schedule Drift",
        "-" * 30,
        f"  Scheduled : {result.scheduled_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"  Actual    : {result.actual_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"  Drift     : {_fmt_seconds(result.drift_seconds)}",
        f"  Limit     : {_fmt_seconds(result.max_drift_seconds)}",
        f"  Status    : {'⚠ EXCEEDED' if result.exceeded else '✓ ok'}",
    ]
    return "\n".join(lines)


def check_and_exit_if_drifted(
    config: DriftConfig,
    scheduled_at: datetime,
    actual_at: Optional[datetime] = None,
    *,
    out=None,
) -> Optional[DriftResult]:
    """Measure drift; print a warning or exit depending on config.

    Returns the DriftResult so callers can inspect it.
    """
    if out is None:
        out = sys.stderr

    if not config.enabled:
        return None

    result = measure_drift(config, scheduled_at, actual_at)

    if result.exceeded:
        print(render_drift_status(result), file=out)
        if not config.warn_only:
            sys.exit(1)

    return result

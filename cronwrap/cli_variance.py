"""CLI rendering helpers for runtime-variance reports."""
from __future__ import annotations

from typing import List

from cronwrap.variance import VarianceReport


def _fmt(value: object, suffix: str = "", width: int = 10) -> str:
    if value is None:
        return "-".rjust(width)
    return f"{value}{suffix}".rjust(width)


def render_variance_report(report: VarianceReport) -> str:
    """Return a single-job variance summary as a human-readable string."""
    stability = "stable" if report.is_stable else "UNSTABLE"
    lines = [
        f"Variance report — {report.job_name}  [{stability}]",
        f"  Samples : {report.sample_count}",
        f"  Mean    : {_fmt(report.mean_seconds, 's').strip()}",
        f"  Std-dev : {_fmt(report.stddev_seconds, 's').strip()}",
        f"  Min     : {_fmt(report.min_seconds, 's').strip()}",
        f"  Max     : {_fmt(report.max_seconds, 's').strip()}",
        f"  CV      : {_fmt(report.cv_percent, '%').strip()}",
    ]
    return "\n".join(lines)


def render_variance_table(reports: List[VarianceReport]) -> str:
    """Render a compact table of variance reports for multiple jobs."""
    if not reports:
        return "No variance data available."

    header = f"{'Job':<30} {'N':>5} {'Mean(s)':>10} {'Stddev(s)':>10} {'CV%':>8} {'Stable':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for r in reports:
        mean = f"{r.mean_seconds:.3f}" if r.mean_seconds is not None else "-"
        stddev = f"{r.stddev_seconds:.3f}" if r.stddev_seconds is not None else "-"
        cv = f"{r.cv_percent:.1f}" if r.cv_percent is not None else "-"
        stable = "yes" if r.is_stable else "NO"
        rows.append(
            f"{r.job_name:<30} {r.sample_count:>5} {mean:>10} {stddev:>10} {cv:>8} {stable:>8}"
        )
    return "\n".join(rows)

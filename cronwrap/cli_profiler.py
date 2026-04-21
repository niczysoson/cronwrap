"""CLI rendering helpers for job profiling data."""
from __future__ import annotations

from typing import List, Optional
from cronwrap.profiler import ProfileSample


def _fmt_seconds(s: Optional[float]) -> str:
    if s is None:
        return "—"
    if s < 1.0:
        return f"{s * 1000:.1f}ms"
    return f"{s:.3f}s"


def _fmt_kb(kb: int) -> str:
    if kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb} KB"


def render_profile_sample(sample: ProfileSample) -> str:
    """Return a single-line summary of a profile sample."""
    wall = _fmt_seconds(sample.wall_seconds)
    user = _fmt_seconds(sample.user_cpu_seconds)
    sys_ = _fmt_seconds(sample.system_cpu_seconds)
    mem = _fmt_kb(sample.max_rss_kb)
    return (
        f"[{sample.job_name}] "
        f"wall={wall} user={user} sys={sys_} mem={mem}"
    )


def render_profile_table(samples: List[ProfileSample]) -> str:
    """Render a table of profile samples."""
    if not samples:
        return "No profile data available."

    header = f"{'Job':<30} {'Wall':>10} {'User CPU':>10} {'Sys CPU':>10} {'Max RSS':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in samples:
        rows.append(
            f"{s.job_name:<30} "
            f"{_fmt_seconds(s.wall_seconds):>10} "
            f"{_fmt_seconds(s.user_cpu_seconds):>10} "
            f"{_fmt_seconds(s.system_cpu_seconds):>10} "
            f"{_fmt_kb(s.max_rss_kb):>10}"
        )
    return "\n".join(rows)

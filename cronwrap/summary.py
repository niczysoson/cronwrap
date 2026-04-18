"""Job run summary formatting for cronwrap."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from cronwrap.history import HistoryEntry
from cronwrap.metrics import JobMetrics, compute_metrics


@dataclass
class JobSummary:
    job_name: str
    total_runs: int
    success_rate: float
    avg_duration: float
    last_status: Optional[str]
    last_ran: Optional[str]

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "total_runs": self.total_runs,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_seconds": round(self.avg_duration, 3),
            "last_status": self.last_status,
            "last_ran": self.last_ran,
        }


def summarise(job_name: str, entries: List[HistoryEntry]) -> JobSummary:
    """Build a JobSummary from a list of history entries for one job."""
    job_entries = [e for e in entries if e.job_name == job_name]
    if not job_entries:
        return JobSummary(
            job_name=job_name,
            total_runs=0,
            success_rate=0.0,
            avg_duration=0.0,
            last_status=None,
            last_ran=None,
        )
    metrics: JobMetrics = compute_metrics(job_entries)
    latest = max(job_entries, key=lambda e: e.started_at)
    return JobSummary(
        job_name=job_name,
        total_runs=metrics.total_runs,
        success_rate=metrics.success_rate,
        avg_duration=metrics.avg_duration_seconds,
        last_status="success" if latest.succeeded() else "failure",
        last_ran=latest.started_at,
    )


def summarise_all(entries: List[HistoryEntry]) -> List[JobSummary]:
    """Return a summary for every distinct job found in entries."""
    names = sorted({e.job_name for e in entries})
    return [summarise(name, entries) for name in names]


def render_summary_table(summaries: List[JobSummary]) -> str:
    """Render summaries as a plain-text table."""
    if not summaries:
        return "No job history available."
    header = f"{'Job':<30} {'Runs':>6} {'Success%':>9} {'AvgDur(s)':>10} {'Last':>8} {'LastRan'}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in summaries:
        pct = f"{s.success_rate * 100:.1f}%"
        dur = f"{s.avg_duration:.2f}"
        status = s.last_status or "-"
        ran = (s.last_ran or "-")[:19]
        rows.append(f"{s.job_name:<30} {s.total_runs:>6} {pct:>9} {dur:>10} {status:>8} {ran}")
    return "\n".join(rows)

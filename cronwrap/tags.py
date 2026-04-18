"""Tag-based filtering and grouping for cron jobs."""
from __future__ import annotations
from typing import List, Dict
from cronwrap.history import JobHistory, HistoryEntry


def get_jobs_by_tag(history: JobHistory, tag: str) -> List[str]:
    """Return distinct job names whose entries include the given tag."""
    matched: set = set()
    for entry in history.entries:
        if tag in (entry.tags or []):
            matched.add(entry.job_name)
    return sorted(matched)


def group_by_tag(history: JobHistory) -> Dict[str, List[str]]:
    """Return a mapping of tag -> sorted list of job names."""
    groups: Dict[str, set] = {}
    for entry in history.entries:
        for tag in (entry.tags or []):
            groups.setdefault(tag, set()).add(entry.job_name)
    return {tag: sorted(names) for tag, names in sorted(groups.items())}


def filter_entries_by_tag(history: JobHistory, tag: str) -> List[HistoryEntry]:
    """Return all history entries that carry the given tag."""
    return [e for e in history.entries if tag in (e.tags or [])]

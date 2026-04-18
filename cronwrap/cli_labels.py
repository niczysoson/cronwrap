"""CLI rendering helpers for label-based job filtering."""
from __future__ import annotations
from typing import Dict, List
from cronwrap.labels import filter_by_selector, group_jobs_by_label


def parse_selector(selector_str: str) -> Dict[str, str]:
    """Parse 'key=value,key2=value2' into a dict."""
    result = {}
    for part in selector_str.split(","):
        part = part.strip()
        if "=" not in part:
            raise ValueError(f"Invalid selector fragment: {part!r}")
        k, v = part.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def render_filtered_jobs(jobs: List[dict], selector_str: str) -> str:
    """Return a text summary of jobs matching the selector."""
    selector = parse_selector(selector_str)
    matched = filter_by_selector(jobs, selector)
    if not matched:
        return f"No jobs match selector: {selector_str}\n"
    lines = [f"Jobs matching [{selector_str}]:\n"]
    for job in matched:
        name = job.get("name", "<unnamed>")
        labels = job.get("labels", {})
        label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
        lines.append(f"  {name}  labels=({label_str})")
    return "\n".join(lines) + "\n"


def render_grouped_jobs(jobs: List[dict], key: str) -> str:
    """Return a text summary of jobs grouped by a label key."""
    groups = group_jobs_by_label(jobs, key)
    if not groups:
        return "No jobs found.\n"
    lines = [f"Jobs grouped by label '{key}':\n"]
    for val, group_jobs in sorted(groups.items()):
        lines.append(f"  [{val}]")
        for job in group_jobs:
            lines.append(f"    - {job.get('name', '<unnamed>')}")
    return "\n".join(lines) + "\n"

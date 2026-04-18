"""Label-based filtering and grouping for cron jobs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        for k, v in self.labels.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError("Label keys and values must be strings")

    def matches(self, selector: Dict[str, str]) -> bool:
        """Return True if all selector key=value pairs are present in labels."""
        return all(self.labels.get(k) == v for k, v in selector.items())

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.labels.get(key, default)

    def to_dict(self) -> Dict[str, str]:
        return dict(self.labels)


def label_set_from_dict(data: dict) -> LabelSet:
    return LabelSet(labels={str(k): str(v) for k, v in data.items()})


def filter_by_selector(jobs: List[dict], selector: Dict[str, str]) -> List[dict]:
    """Filter job config dicts by a label selector."""
    result = []
    for job in jobs:
        raw = job.get("labels", {})
        ls = LabelSet(labels=raw)
        if ls.matches(selector):
            result.append(job)
    return result


def group_jobs_by_label(jobs: List[dict], key: str) -> Dict[str, List[dict]]:
    """Group job config dicts by the value of a specific label key."""
    groups: Dict[str, List[dict]] = {}
    for job in jobs:
        raw = job.get("labels", {})
        ls = LabelSet(labels=raw)
        val = ls.get(key, "__unset__")
        groups.setdefault(val, []).append(job)
    return groups

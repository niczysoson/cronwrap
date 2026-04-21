"""CLI command integration for the profiler (used by cli.py cmd_profile)."""
from __future__ import annotations

import json
import os
from typing import List, Optional

from cronwrap.profiler import ProfileSample
from cronwrap.cli_profiler import render_profile_table, render_profile_sample

_DEFAULT_STORE = os.path.join(
    os.environ.get("CRONWRAP_DATA_DIR", ".cronwrap"), "profiles.jsonl"
)


def _load_samples(path: str) -> List[ProfileSample]:
    samples: List[ProfileSample] = []
    if not os.path.exists(path):
        return samples
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    samples.append(ProfileSample.from_dict(json.loads(line)))
                except (KeyError, ValueError):
                    pass
    return samples


def save_sample(sample: ProfileSample, path: str = _DEFAULT_STORE) -> None:
    """Append a single profile sample to the JSONL store."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(sample.to_dict()) + "\n")


def cmd_profile(
    job_name: Optional[str] = None,
    path: str = _DEFAULT_STORE,
    last: int = 20,
) -> str:
    """Return a rendered profile table, optionally filtered by job_name."""
    samples = _load_samples(path)
    if job_name:
        samples = [s for s in samples if s.job_name == job_name]
    samples = samples[-last:]
    return render_profile_table(samples)


def cmd_profile_last(
    job_name: str,
    path: str = _DEFAULT_STORE,
) -> Optional[str]:
    """Return a one-line summary of the most recent profile for *job_name*."""
    samples = [s for s in _load_samples(path) if s.job_name == job_name]
    if not samples:
        return None
    return render_profile_sample(samples[-1])

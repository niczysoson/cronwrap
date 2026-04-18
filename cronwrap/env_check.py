"""Pre-flight environment variable checks for cron jobs."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EnvCheckResult:
    missing: List[str] = field(default_factory=list)
    empty: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.empty

    def summary(self) -> str:
        parts = []
        if self.missing:
            parts.append("Missing: " + ", ".join(self.missing))
        if self.empty:
            parts.append("Empty: " + ", ".join(self.empty))
        return "; ".join(parts) if parts else "All required env vars present."


def check_env(
    required: List[str],
    allow_empty: bool = False,
) -> EnvCheckResult:
    """Check that all *required* environment variables are set (and non-empty).

    Args:
        required: Variable names that must exist.
        allow_empty: When False (default) a variable that is set but blank
                     is reported under *empty*.
    """
    result = EnvCheckResult()
    for name in required:
        if name not in os.environ:
            result.missing.append(name)
        elif not allow_empty and os.environ[name].strip() == "":
            result.empty.append(name)
    return result


def check_env_from_dict(cfg: dict) -> EnvCheckResult:
    """Convenience wrapper that reads config from a dict.

    Expected keys:
        required_env  – list of variable names (required)
        allow_empty   – bool (optional, default False)
    """
    required: List[str] = cfg.get("required_env", [])
    allow_empty: bool = bool(cfg.get("allow_empty", False))
    return check_env(required, allow_empty=allow_empty)

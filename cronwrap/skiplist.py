"""Skip-list: allow certain exit codes or conditions to be treated as non-failures."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class SkipConfig:
    """Configuration for skip-list behaviour."""
    exit_codes: List[int] = field(default_factory=list)
    stdout_patterns: List[str] = field(default_factory=list)
    stderr_patterns: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.exit_codes, list):
            raise ValueError("exit_codes must be a list")
        for code in self.exit_codes:
            if not isinstance(code, int):
                raise ValueError(f"exit code must be int, got {code!r}")
        if not isinstance(self.stdout_patterns, list):
            raise ValueError("stdout_patterns must be a list")
        if not isinstance(self.stderr_patterns, list):
            raise ValueError("stderr_patterns must be a list")

    def should_skip(self, exit_code: int, stdout: str = "", stderr: str = "") -> bool:
        """Return True if this result should be treated as skipped (non-failure)."""
        if not self.enabled:
            return False
        if exit_code in self.exit_codes:
            return True
        for pattern in self.stdout_patterns:
            if pattern in stdout:
                return True
        for pattern in self.stderr_patterns:
            if pattern in stderr:
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "exit_codes": list(self.exit_codes),
            "stdout_patterns": list(self.stdout_patterns),
            "stderr_patterns": list(self.stderr_patterns),
            "enabled": self.enabled,
        }


def skiplist_from_dict(data: dict) -> SkipConfig:
    return SkipConfig(
        exit_codes=data.get("exit_codes", []),
        stdout_patterns=data.get("stdout_patterns", []),
        stderr_patterns=data.get("stderr_patterns", []),
        enabled=data.get("enabled", True),
    )

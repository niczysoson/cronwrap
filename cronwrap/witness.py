"""Witness module — record and verify expected output patterns for cron jobs.

A 'witness' captures what a job is expected to produce (stdout/stderr patterns,
exit codes) and flags deviations from those expectations over time.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class WitnessRule:
    """A single expectation about a job's output."""

    field: str          # 'stdout', 'stderr', or 'exit_code'
    pattern: str        # regex pattern (for text fields) or exact string (for exit_code)
    required: bool = True  # if True, absence of match is a violation
    forbidden: bool = False  # if True, presence of match is a violation

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "pattern": self.pattern,
            "required": self.required,
            "forbidden": self.forbidden,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WitnessRule":
        return cls(
            field=d["field"],
            pattern=d["pattern"],
            required=d.get("required", True),
            forbidden=d.get("forbidden", False),
        )


@dataclass
class WitnessViolation:
    """Describes a single rule violation."""

    rule: WitnessRule
    reason: str

    def __str__(self) -> str:
        return f"[{self.rule.field}] {self.reason} (pattern={self.rule.pattern!r})"


@dataclass
class WitnessResult:
    """Outcome of checking a job result against all witness rules."""

    violations: List[WitnessViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return "witness: all expectations met"
        lines = [f"witness: {len(self.violations)} violation(s)"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


@dataclass
class WitnessConfig:
    """Collection of rules that define expected job behaviour."""

    rules: List[WitnessRule] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        for rule in self.rules:
            if rule.field not in ("stdout", "stderr", "exit_code"):
                raise ValueError(
                    f"Invalid witness field {rule.field!r}; "
                    "expected 'stdout', 'stderr', or 'exit_code'"
                )
            if rule.required and rule.forbidden:
                raise ValueError(
                    "A rule cannot be both required and forbidden."
                )

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "rules": [r.to_dict() for r in self.rules],
        }


def witness_from_dict(d: dict) -> WitnessConfig:
    """Build a WitnessConfig from a plain dictionary (e.g. from YAML/JSON config)."""
    rules = [WitnessRule.from_dict(r) for r in d.get("rules", [])]
    return WitnessConfig(
        rules=rules,
        enabled=d.get("enabled", True),
    )


def check_witness(config: WitnessConfig, stdout: str, stderr: str, exit_code: int) -> WitnessResult:
    """Evaluate all witness rules against the provided job output.

    Args:
        config:    The WitnessConfig containing the rules to evaluate.
        stdout:    The captured standard output of the job.
        stderr:    The captured standard error of the job.
        exit_code: The integer exit code returned by the job.

    Returns:
        A WitnessResult describing any violations found.
    """
    result = WitnessResult()

    if not config.enabled:
        return result

    field_values: dict = {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": str(exit_code),
    }

    for rule in config.rules:
        value = field_values.get(rule.field, "")
        matched = bool(re.search(rule.pattern, value))

        if rule.required and not matched:
            result.violations.append(
                WitnessViolation(
                    rule=rule,
                    reason=f"expected pattern not found in {rule.field}",
                )
            )
        elif rule.forbidden and matched:
            result.violations.append(
                WitnessViolation(
                    rule=rule,
                    reason=f"forbidden pattern found in {rule.field}",
                )
            )

    return result

"""Input validation for job commands and configurations."""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import List, Optional


_DANGEROUS_PATTERNS = [
    r";\s*rm\s+-rf",
    r"\|\s*sh",
    r"`[^`]+`",
    r"\$\([^)]+\)",
]


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.valid and not self.errors

    def summary(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        return "\n".join(lines) if lines else "  OK"


def validate_command(command: str, allow_shell: bool = False) -> ValidationResult:
    """Validate a shell command string for safety and parseability."""
    errors: List[str] = []
    warnings: List[str] = []

    if not command or not command.strip():
        return ValidationResult(valid=False, errors=["Command must not be empty."])

    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            warnings.append(f"Potentially dangerous pattern detected: {pattern!r}")

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return ValidationResult(valid=False, errors=[f"Command parse error: {exc}"])

    if not tokens:
        return ValidationResult(valid=False, errors=["Command resolved to empty token list."])

    if not allow_shell and any(t in (";", "&&", "||") for t in tokens):
        errors.append("Shell operators detected; set allow_shell=True to permit them.")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_job_name(name: str) -> ValidationResult:
    """Validate a job name (alphanumeric, hyphens, underscores)."""
    if not name or not name.strip():
        return ValidationResult(valid=False, errors=["Job name must not be empty."])
    if not re.fullmatch(r"[\w][\w\-]*", name):
        return ValidationResult(
            valid=False,
            errors=[f"Invalid job name {name!r}: use letters, digits, hyphens, underscores only."],
        )
    return ValidationResult(valid=True)


def validation_from_dict(data: dict) -> ValidationResult:
    """Run all validations from a config dict."""
    command = data.get("command", "")
    name = data.get("name", "")
    allow_shell = bool(data.get("allow_shell", False))

    r_cmd = validate_command(command, allow_shell=allow_shell)
    r_name = validate_job_name(name)

    errors = r_cmd.errors + r_name.errors
    warnings = r_cmd.warnings + r_name.warnings
    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

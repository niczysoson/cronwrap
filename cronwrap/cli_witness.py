"""CLI rendering for witness rule violations and summaries."""

from __future__ import annotations

from typing import List

from cronwrap.witness import WitnessRule, WitnessViolation, evaluate_rules
from cronwrap.runner import RunResult


_SYMBOL_OK = "\u2713"   # ✓
_SYMBOL_FAIL = "\u2717" # ✗
_SYMBOL_WARN = "\u26a0" # ⚠


def _severity_symbol(severity: str) -> str:
    """Return a display symbol for the given severity level."""
    if severity == "error":
        return _SYMBOL_FAIL
    if severity == "warn":
        return _SYMBOL_WARN
    return _SYMBOL_OK


def render_witness_rules(rules: List[WitnessRule]) -> str:
    """Render a summary table of configured witness rules.

    Args:
        rules: List of WitnessRule instances to display.

    Returns:
        A formatted multi-line string.
    """
    if not rules:
        return "No witness rules configured."

    lines = ["Witness Rules:", "-" * 48]
    for rule in rules:
        enabled_flag = "on" if rule.enabled else "off"
        lines.append(
            f"  [{enabled_flag:3s}] {rule.name:<24s}  "
            f"severity={rule.severity}  "
            f"pattern={'<regex>' if rule.pattern else 'none'}"
        )
    lines.append("-" * 48)
    lines.append(f"  Total: {len(rules)} rule(s)")
    return "\n".join(lines)


def render_witness_violations(violations: List[WitnessViolation]) -> str:
    """Render a list of witness violations in a human-readable format.

    Args:
        violations: List of WitnessViolation objects to display.

    Returns:
        A formatted multi-line string.
    """
    if not violations:
        return f"{_SYMBOL_OK} No witness violations detected."

    lines = [f"{_SYMBOL_FAIL} Witness violations ({len(violations)}):", "-" * 52]
    for v in violations:
        sym = _severity_symbol(v.severity)
        lines.append(f"  {sym} [{v.severity.upper():<5s}] {v.rule_name}")
        lines.append(f"       {v.message}")
    lines.append("-" * 52)
    return "\n".join(lines)


def check_and_exit_if_violated(
    rules: List[WitnessRule],
    result: RunResult,
    *,
    exit_fn=None,
) -> List[WitnessViolation]:
    """Evaluate witness rules against a RunResult and exit if errors are found.

    Only violations with severity ``'error'`` trigger a non-zero exit.  Warnings
    are printed but do not cause an exit.

    Args:
        rules:    Configured witness rules.
        result:   The RunResult to evaluate.
        exit_fn:  Callable used to exit (defaults to ``sys.exit``).  Useful for
                  testing without actually terminating the process.

    Returns:
        The full list of violations (both warnings and errors).
    """
    import sys

    if exit_fn is None:
        exit_fn = sys.exit

    violations = evaluate_rules(rules, result)

    if not violations:
        return violations

    print(render_witness_violations(violations))

    errors = [v for v in violations if v.severity == "error"]
    if errors:
        exit_fn(1)

    return violations

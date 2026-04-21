"""CLI helpers for displaying runtime budget status."""
from __future__ import annotations

from cronwrap.budgets import BudgetConfig, BudgetResult


def _fmt_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m {secs:.0f}s"


def render_budget_config(cfg: BudgetConfig) -> str:
    """Return a human-readable summary of a budget configuration."""
    lines = ["Runtime Budget Configuration"]
    lines.append(f"  enabled    : {'yes' if cfg.enabled else 'no'}")
    lines.append(f"  max        : {_fmt_seconds(cfg.max_seconds)}")
    if cfg.warn_at_seconds is not None:
        lines.append(f"  warn after : {_fmt_seconds(cfg.warn_at_seconds)}")
    else:
        lines.append("  warn after : (none)")
    return "\n".join(lines)


def render_budget_result(result: BudgetResult) -> str:
    """Return a human-readable summary of a budget evaluation result."""
    if not result.budget.enabled:
        return "[budget] disabled"
    if result.over_budget:
        symbol = "✗"
        label = "OVER BUDGET"
    elif result.warned:
        symbol = "!"
        label = "WARNING"
    else:
        symbol = "✓"
        label = "OK"
    return (
        f"[budget] {symbol} {label} — "
        f"elapsed {_fmt_seconds(result.elapsed_seconds)} / "
        f"limit {_fmt_seconds(result.budget.max_seconds)}"
    )


def check_and_exit_if_over_budget(result: BudgetResult) -> None:
    """Print budget status and raise SystemExit(1) when over budget."""
    print(render_budget_result(result))
    if result.over_budget:
        raise SystemExit(1)

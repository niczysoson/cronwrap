"""Runtime budget enforcement: fail a job if it exceeds a wall-clock budget."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetConfig:
    """Configuration for a runtime budget."""
    max_seconds: float
    warn_at_seconds: Optional[float] = None
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        if self.warn_at_seconds is not None:
            if self.warn_at_seconds <= 0:
                raise ValueError("warn_at_seconds must be positive")
            if self.warn_at_seconds >= self.max_seconds:
                raise ValueError("warn_at_seconds must be less than max_seconds")


def budget_from_dict(d: dict) -> BudgetConfig:
    """Construct a BudgetConfig from a plain dictionary."""
    return BudgetConfig(
        max_seconds=float(d["max_seconds"]),
        warn_at_seconds=float(d["warn_at_seconds"]) if "warn_at_seconds" in d else None,
        enabled=bool(d.get("enabled", True)),
    )


@dataclass
class BudgetResult:
    elapsed_seconds: float
    over_budget: bool
    warned: bool
    budget: BudgetConfig

    @property
    def summary(self) -> str:
        if not self.budget.enabled:
            return "budget disabled"
        if self.over_budget:
            return (
                f"OVER BUDGET: {self.elapsed_seconds:.1f}s elapsed, "
                f"limit {self.budget.max_seconds:.1f}s"
            )
        if self.warned:
            return (
                f"WARNING: {self.elapsed_seconds:.1f}s elapsed, "
                f"warn threshold {self.budget.warn_at_seconds:.1f}s"
            )
        return f"OK: {self.elapsed_seconds:.1f}s elapsed (limit {self.budget.max_seconds:.1f}s)"


class BudgetTimer:
    """Context-manager that tracks elapsed time against a BudgetConfig."""

    def __init__(self, config: BudgetConfig) -> None:
        self._config = config
        self._start: float = 0.0
        self._end: Optional[float] = None

    def __enter__(self) -> "BudgetTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *_) -> None:
        self._end = time.monotonic()

    @property
    def elapsed(self) -> float:
        end = self._end if self._end is not None else time.monotonic()
        return end - self._start

    def evaluate(self) -> BudgetResult:
        elapsed = self.elapsed
        cfg = self._config
        if not cfg.enabled:
            return BudgetResult(elapsed, False, False, cfg)
        over = elapsed > cfg.max_seconds
        warned = (
            not over
            and cfg.warn_at_seconds is not None
            and elapsed >= cfg.warn_at_seconds
        )
        return BudgetResult(elapsed, over, warned, cfg)

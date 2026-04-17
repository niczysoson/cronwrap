"""Cron expression parsing and schedule validation utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional


class CronExpression:
    """Represents and validates a cron expression."""

    FIELDS = ["minute", "hour", "day", "month", "weekday"]
    RANGES = {
        "minute": (0, 59),
        "hour": (0, 23),
        "day": (1, 31),
        "month": (1, 12),
        "weekday": (0, 6),
    }

    def __init__(self, expression: str) -> None:
        self.expression = expression.strip()
        self._parts: list[str] = []
        self._parse()

    def _parse(self) -> None:
        parts = self.expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression '{self.expression}': expected 5 fields, got {len(parts)}"
            )
        self._parts = parts
        for part, field in zip(parts, self.FIELDS):
            self._validate_field(part, field)

    def _validate_field(self, value: str, field: str) -> None:
        lo, hi = self.RANGES[field]
        if value == "*":
            return
        try:
            if "/" in value:
                base, step = value.split("/", 1)
                if base != "*":
                    int(base)
                step_val = int(step)
                if step_val < 1:
                    raise ValueError("Step must be >= 1")
            elif "-" in value:
                a, b = value.split("-", 1)
                if not (lo <= int(a) <= hi and lo <= int(b) <= hi):
                    raise ValueError(f"{value} out of range [{lo},{hi}]")
            elif "," in value:
                for v in value.split(","):
                    if not (lo <= int(v) <= hi):
                        raise ValueError(f"{v} out of range [{lo},{hi}]")
            else:
                if not (lo <= int(value) <= hi):
                    raise ValueError(f"{value} out of range [{lo},{hi}]")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid value '{value}' for field '{field}': {exc}") from exc

    def matches(self, dt: Optional[datetime] = None) -> bool:
        """Return True if *dt* (defaults to now) matches this expression."""
        if dt is None:
            dt = datetime.now()
        values = {
            "minute": dt.minute,
            "hour": dt.hour,
            "day": dt.day,
            "month": dt.month,
            "weekday": dt.weekday(),
        }
        for part, field in zip(self._parts, self.FIELDS):
            if not self._field_matches(part, values[field], self.RANGES[field]):
                return False
        return True

    @staticmethod
    def _field_matches(part: str, value: int, rng: tuple[int, int]) -> bool:
        lo, hi = rng
        if part == "*":
            return True
        if "/" in part:
            base, step = part.split("/", 1)
            start = lo if base == "*" else int(base)
            return (value - start) % int(step) == 0 and value >= start
        if "-" in part:
            a, b = part.split("-", 1)
            return int(a) <= value <= int(b)
        if "," in part:
            return value in {int(v) for v in part.split(",")}
        return value == int(part)

    def __repr__(self) -> str:  # pragma: no cover
        return f"CronExpression({self.expression!r})"

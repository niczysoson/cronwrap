"""Job configuration loading from TOML / dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cronwrap.scheduler import CronExpression


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    retries: int = 0
    timeout: int = 3600
    alert_on_failure: bool = True
    tags: list[str] = field(default_factory=list)

    # Validated expression (populated post-init)
    _expr: CronExpression = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Job name must not be empty")
        if not self.command:
            raise ValueError("Job command must not be empty")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        self._expr = CronExpression(self.schedule)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobConfig":
        """Create a JobConfig from a plain dictionary (e.g. parsed TOML)."""
        required = {"name", "command", "schedule"}
        missing = required - data.keys()
        if missing:
            raise KeyError(f"Missing required job fields: {missing}")
        return cls(
            name=data["name"],
            command=data["command"],
            schedule=data["schedule"],
            retries=int(data.get("retries", 0)),
            timeout=int(data.get("timeout", 3600)),
            alert_on_failure=bool(data.get("alert_on_failure", True)),
            tags=list(data.get("tags", [])),
        )

    def is_due(self) -> bool:
        """Return True if the job should run right now."""
        return self._expr.matches()

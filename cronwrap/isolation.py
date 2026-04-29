"""Job isolation: run jobs with restricted environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class IsolationConfig:
    """Configuration for environment variable isolation."""

    enabled: bool = True
    # If set, only these env vars are passed through
    allowlist: List[str] = field(default_factory=list)
    # These env vars are always stripped, even if in allowlist
    denylist: List[str] = field(default_factory=list)
    # Extra env vars injected into the job environment
    inject: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if not isinstance(self.allowlist, list):
            raise ValueError("allowlist must be a list")
        if not isinstance(self.denylist, list):
            raise ValueError("denylist must be a list")
        if not isinstance(self.inject, dict):
            raise ValueError("inject must be a dict")

    def build_env(self, base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Return the environment dict to pass to the subprocess."""
        if base_env is None:
            base_env = dict(os.environ)

        if not self.enabled:
            env = dict(base_env)
        elif self.allowlist:
            env = {k: v for k, v in base_env.items() if k in self.allowlist}
        else:
            env = dict(base_env)

        for key in self.denylist:
            env.pop(key, None)

        env.update(self.inject)
        return env

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "allowlist": list(self.allowlist),
            "denylist": list(self.denylist),
            "inject": dict(self.inject),
        }


def isolation_from_dict(data: dict) -> IsolationConfig:
    """Build an IsolationConfig from a plain dictionary."""
    return IsolationConfig(
        enabled=bool(data.get("enabled", True)),
        allowlist=list(data.get("allowlist", [])),
        denylist=list(data.get("denylist", [])),
        inject=dict(data.get("inject", {})),
    )

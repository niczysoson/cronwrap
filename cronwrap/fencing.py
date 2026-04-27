"""Fencing: prevent a job from running on unexpected hosts."""
from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FenceConfig:
    """Configuration for host-based fencing."""

    allowed_hosts: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.allowed_hosts, list):
            raise ValueError("allowed_hosts must be a list")
        if not all(isinstance(h, str) and h.strip() for h in self.allowed_hosts):
            raise ValueError("each entry in allowed_hosts must be a non-empty string")


@dataclass
class FenceResult:
    allowed: bool
    current_host: str
    allowed_hosts: List[str]

    def summary(self) -> str:
        if self.allowed:
            return f"Host '{self.current_host}' is permitted to run this job."
        hosts = ", ".join(self.allowed_hosts) if self.allowed_hosts else "(none)"
        return (
            f"Host '{self.current_host}' is NOT in the allowed list: [{hosts}]."
        )


def fence_from_dict(data: dict) -> FenceConfig:
    """Build a FenceConfig from a plain dict (e.g. loaded from YAML/JSON)."""
    return FenceConfig(
        allowed_hosts=data.get("allowed_hosts", []),
        enabled=data.get("enabled", True),
    )


def check_fence(config: FenceConfig, hostname: Optional[str] = None) -> FenceResult:
    """Return a FenceResult indicating whether the current host is allowed."""
    current = hostname or socket.gethostname()
    if not config.enabled or not config.allowed_hosts:
        # Fencing disabled or no list configured — always allow.
        return FenceResult(allowed=True, current_host=current, allowed_hosts=config.allowed_hosts)
    allowed = current in config.allowed_hosts
    return FenceResult(allowed=allowed, current_host=current, allowed_hosts=config.allowed_hosts)

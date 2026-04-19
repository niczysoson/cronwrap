"""Alert manager: route job failure/recovery events to named alert channels."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

AlertHandler = Callable[[str, str, dict], None]  # (channel, event, payload)

_REGISTRY: Dict[str, AlertHandler] = {}


def register_channel(name: str, handler: AlertHandler) -> None:
    """Register a named alert channel handler."""
    _REGISTRY[name] = handler


def get_channel(name: str) -> Optional[AlertHandler]:
    return _REGISTRY.get(name)


@dataclass
class AlertRule:
    channel: str
    events: List[str] = field(default_factory=lambda: ["failure"])
    min_exit_code: int = 1
    enabled: bool = True


@dataclass
class AlertManagerConfig:
    rules: List[AlertRule] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "AlertManagerConfig":
        rules = [
            AlertRule(
                channel=r["channel"],
                events=r.get("events", ["failure"]),
                min_exit_code=r.get("min_exit_code", 1),
                enabled=r.get("enabled", True),
            )
            for r in d.get("rules", [])
        ]
        return AlertManagerConfig(rules=rules)


def dispatch(config: AlertManagerConfig, event: str, payload: dict) -> List[str]:
    """Dispatch an event through matching rules. Returns list of channels notified."""
    notified: List[str] = []
    exit_code = payload.get("exit_code", 0)
    for rule in config.rules:
        if not rule.enabled:
            continue
        if event not in rule.events:
            continue
        if exit_code < rule.min_exit_code:
            continue
        handler = get_channel(rule.channel)
        if handler is None:
            logger.warning("Alert channel %r not registered", rule.channel)
            continue
        try:
            handler(rule.channel, event, payload)
            notified.append(rule.channel)
        except Exception as exc:  # pragma: no cover
            logger.error("Alert channel %r raised: %s", rule.channel, exc)
    return notified

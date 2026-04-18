"""Notification hooks for cronwrap job lifecycle events."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwrap.runner import RunResult

logger = logging.getLogger(__name__)

NotifyHook = Callable[[str, RunResult], None]


@dataclass
class NotifyConfig:
    """Configuration for notification hooks."""
    on_success: List[NotifyHook] = field(default_factory=list)
    on_failure: List[NotifyHook] = field(default_factory=list)
    on_retry: List[NotifyHook] = field(default_factory=list)


def _safe_call(hook: NotifyHook, job_name: str, result: RunResult) -> None:
    """Call a hook, swallowing exceptions so they never break the job."""
    try:
        hook(job_name, result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Notification hook %r raised: %s", hook, exc)


def notify_success(cfg: NotifyConfig, job_name: str, result: RunResult) -> None:
    """Fire all on_success hooks."""
    for hook in cfg.on_success:
        _safe_call(hook, job_name, result)


def notify_failure(cfg: NotifyConfig, job_name: str, result: RunResult) -> None:
    """Fire all on_failure hooks."""
    for hook in cfg.on_failure:
        _safe_call(hook, job_name, result)


def notify_retry(cfg: NotifyConfig, job_name: str, result: RunResult) -> None:
    """Fire all on_retry hooks."""
    for hook in cfg.on_retry:
        _safe_call(hook, job_name, result)


def log_hook(job_name: str, result: RunResult) -> None:
    """Built-in hook that logs the result at INFO level."""
    logger.info(
        "[%s] exit=%s duration=%.3fs stdout=%r",
        job_name,
        result.returncode,
        result.duration,
        result.stdout[:120] if result.stdout else "",
    )

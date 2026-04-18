"""Deadline helpers — integrate timeout with the job runner."""
from __future__ import annotations

from typing import Callable, Optional

from cronwrap.timeout import TimeoutConfig, TimeoutExpired, timeout_context
from cronwrap.runner import RunResult


def run_with_deadline(
    fn: Callable[[], RunResult],
    cfg: Optional[TimeoutConfig],
) -> RunResult:
    """Run *fn* inside a timeout context.

    If the timeout expires a synthetic failed RunResult is returned instead
    of propagating the exception, so the existing retry/alert pipeline can
    handle it uniformly.
    """
    try:
        with timeout_context(cfg):
            return fn()
    except TimeoutExpired as exc:
        return RunResult(
            returncode=124,  # same convention as GNU `timeout`
            stdout="",
            stderr=str(exc),
            duration=cfg.seconds if cfg else 0,
            attempts=1,
        )


def deadline_from_dict(data: dict) -> Optional[TimeoutConfig]:
    """Build a TimeoutConfig from a plain dict (e.g. parsed YAML/JSON).

    Expects optional keys: ``timeout_seconds``, ``kill_on_expire``.
    Returns None when ``timeout_seconds`` is absent or zero.
    """
    seconds = int(data.get("timeout_seconds", 0))
    if not seconds:
        return None
    kill = bool(data.get("kill_on_expire", True))
    return TimeoutConfig(seconds=seconds, kill_on_expire=kill)

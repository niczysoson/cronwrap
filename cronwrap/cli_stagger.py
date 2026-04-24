"""CLI helpers for displaying and applying stagger configuration."""
from __future__ import annotations

from cronwrap.stagger import StaggerConfig


def render_stagger_status(cfg: StaggerConfig) -> str:
    """Return a human-readable summary of the stagger configuration."""
    lines: list[str] = []
    if not cfg.enabled:
        lines.append("Stagger: disabled")
        return "\n".join(lines)

    delay = cfg.delay()
    lines.append("Stagger: enabled")
    lines.append(f"  Window : {cfg.window_seconds}s")
    lines.append(f"  Seed   : {cfg.seed!r}")
    lines.append(f"  Delay  : {delay:.3f}s")
    return "\n".join(lines)


def check_and_apply_stagger(cfg: StaggerConfig) -> float:
    """Sleep for the stagger delay (if enabled) and return the delay applied.

    Callers can use the returned value for logging.
    """
    delay = cfg.sleep()
    return delay

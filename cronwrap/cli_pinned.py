"""CLI helpers for pinned job config."""
from __future__ import annotations

import sys

from cronwrap.pinned import PinnedConfig


def render_pin_status(cfg: PinnedConfig) -> str:
    if not cfg.enabled:
        return f"[pin] {cfg.job_name}: disabled"
    saved = cfg.saved_hash()
    current = cfg.current_hash()
    if saved is None:
        return f"[pin] {cfg.job_name}: no pin saved (current={current[:12]})"
    if saved == current:
        return f"[pin] {cfg.job_name}: OK (hash={current[:12]})"
    return (
        f"[pin] {cfg.job_name}: CHANGED "
        f"saved={saved[:12]} current={current[:12]}"
    )


def check_and_exit_if_changed(cfg: PinnedConfig) -> None:
    """Print status and exit with code 1 if config has changed."""
    print(render_pin_status(cfg))
    if cfg.is_changed():
        print(
            f"[pin] Aborting: config for '{cfg.job_name}' has changed since last pin.",
            file=sys.stderr,
        )
        sys.exit(1)

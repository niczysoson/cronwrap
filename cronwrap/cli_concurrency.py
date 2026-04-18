"""CLI helpers for concurrency status."""
from __future__ import annotations

import sys
from cronwrap.concurrency import ConcurrencyConfig, ConcurrencyError, acquire_slot, current_count


def render_concurrency_status(job_name: str, cfg: ConcurrencyConfig) -> str:
    count = current_count(job_name, cfg)
    lines = [
        f"Concurrency limit : {cfg.max_concurrent}",
        f"Active instances  : {count}",
        f"Slots available   : {max(0, cfg.max_concurrent - count)}",
    ]
    return "\n".join(lines)


def check_and_exit_if_at_limit(job_name: str, cfg: ConcurrencyConfig) -> str | None:
    """Acquire a slot or print an error and exit.

    Returns the slot path on success.
    """
    try:
        slot = acquire_slot(job_name, cfg)
        return slot
    except ConcurrencyError as exc:
        print(f"[cronwrap] concurrency limit reached: {exc}", file=sys.stderr)
        sys.exit(75)  # EX_TEMPFAIL

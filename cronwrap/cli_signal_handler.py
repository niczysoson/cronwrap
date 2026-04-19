"""CLI helpers for signal-handler status."""

from __future__ import annotations

import signal as _signal
from typing import List

from cronwrap.signal_handler import SignalHandlerConfig


def _sig_name(signum: int) -> str:
    try:
        return _signal.Signals(signum).name
    except ValueError:
        return str(signum)


def render_signal_config(config: SignalHandlerConfig) -> str:
    """Return a human-readable summary of the signal handler config."""
    names = ", ".join(_sig_name(s) for s in config.signals)
    has_cb = "yes" if config.on_signal is not None else "no"
    lines = [
        "Signal Handler Configuration",
        f"  Watched signals : {names}",
        f"  Custom callback : {has_cb}",
    ]
    return "\n".join(lines)


def render_signal_status(triggered: List[int]) -> str:
    """Return a summary of signals received so far."""
    if not triggered:
        return "No signals received."
    entries = ", ".join(f"{_sig_name(s)} ({s})" for s in triggered)
    return f"Signals received: {entries}"

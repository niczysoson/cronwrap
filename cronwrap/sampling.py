"""Sampling — run a cron job only a fraction of the time.

Useful for gradually rolling out a job or reducing load by executing
only a statistical sample of scheduled invocations.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SamplingConfig:
    """Configuration for probabilistic job sampling.

    Attributes:
        rate: Probability of running, in the range (0.0, 1.0].
              1.0 means always run (sampling disabled effectively).
        enabled: Master switch; when False the job always runs.
        seed: Optional RNG seed for deterministic testing.
    """
    rate: float = 1.0
    enabled: bool = True
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not (0.0 < self.rate <= 1.0):
            raise ValueError(f"rate must be in (0.0, 1.0], got {self.rate}")
        self._rng = random.Random(self.seed)

    def should_run(self) -> bool:
        """Return True if this invocation should proceed."""
        if not self.enabled:
            return True
        return self._rng.random() < self.rate

    def to_dict(self) -> dict:
        return {"rate": self.rate, "enabled": self.enabled}


def sampling_from_dict(data: dict) -> SamplingConfig:
    """Build a SamplingConfig from a plain dictionary (e.g. parsed YAML)."""
    return SamplingConfig(
        rate=float(data.get("rate", 1.0)),
        enabled=bool(data.get("enabled", True)),
        seed=data.get("seed"),
    )


def render_sampling_status(cfg: SamplingConfig) -> str:
    """Return a human-readable one-liner describing the sampling config."""
    if not cfg.enabled:
        return "Sampling: disabled (job always runs)"
    pct = cfg.rate * 100
    if cfg.rate >= 1.0:
        return "Sampling: 100% — job always runs"
    return f"Sampling: {pct:.1f}% chance of running each invocation"


def check_and_exit_if_sampled_out(
    cfg: SamplingConfig,
    *,
    verbose: bool = False,
) -> bool:
    """Return True (and optionally print a message) when the job should be skipped.

    Callers can use the return value to exit early:

        if check_and_exit_if_sampled_out(cfg):
            sys.exit(0)
    """
    if cfg.should_run():
        return False
    if verbose:
        pct = cfg.rate * 100
        print(f"[cronwrap] Skipped by sampling (rate={pct:.1f}%)")
    return True

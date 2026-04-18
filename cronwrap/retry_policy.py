"""Flexible retry policy configuration and evaluation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 5.0
    backoff_factor: float = 1.0  # multiplier applied after each attempt
    retry_on_exit_codes: Optional[List[int]] = None  # None = retry on any failure

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")

    def should_retry(self, attempt: int, exit_code: int) -> bool:
        """Return True if another attempt should be made."""
        if attempt >= self.max_attempts:
            return False
        if self.retry_on_exit_codes is not None:
            return exit_code in self.retry_on_exit_codes
        return exit_code != 0

    def wait_seconds(self, attempt: int) -> float:
        """Return how long to wait before the given attempt (0-indexed)."""
        if attempt == 0:
            return 0.0
        return self.delay_seconds * (self.backoff_factor ** (attempt - 1))

    def to_dict(self) -> dict:
        return {
            "max_attempts": self.max_attempts,
            "delay_seconds": self.delay_seconds,
            "backoff_factor": self.backoff_factor,
            "retry_on_exit_codes": self.retry_on_exit_codes,
        }


def retry_policy_from_dict(data: dict) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=int(data.get("max_attempts", 3)),
        delay_seconds=float(data.get("delay_seconds", 5.0)),
        backoff_factor=float(data.get("backoff_factor", 1.0)),
        retry_on_exit_codes=data.get("retry_on_exit_codes"),
    )


def sleep_between_attempts(policy: RetryPolicy, attempt: int) -> None:
    """Sleep for the appropriate delay before *attempt* (0-indexed)."""
    secs = policy.wait_seconds(attempt)
    if secs > 0:
        time.sleep(secs)

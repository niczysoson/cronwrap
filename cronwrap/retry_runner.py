"""Execute a command with a RetryPolicy, recording each attempt."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from cronwrap.runner import RunResult, run as _run
from cronwrap.retry_policy import RetryPolicy, sleep_between_attempts


@dataclass
class RetryRunResult:
    attempts: List[RunResult] = field(default_factory=list)

    @property
    def final(self) -> RunResult:
        return self.attempts[-1]

    @property
    def succeeded(self) -> bool:
        return bool(self.attempts) and self.attempts[-1].exit_code == 0

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)


def run_with_retry(
    cmd: str,
    policy: RetryPolicy,
    *,
    timeout: float | None = None,
) -> RetryRunResult:
    """Run *cmd* up to policy.max_attempts times, honouring delay/backoff."""
    result = RetryRunResult()
    for attempt in range(policy.max_attempts):
        sleep_between_attempts(policy, attempt)
        outcome: RunResult = _run(cmd, timeout=timeout)
        result.attempts.append(outcome)
        if outcome.exit_code == 0:
            break
        if not policy.should_retry(attempt + 1, outcome.exit_code):
            break
    return result

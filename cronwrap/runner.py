"""Core runner logic for executing cron job commands with retry support."""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cronwrap.history import HistoryEntry, JobHistory
from cronwrap.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RunResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    attempts: int
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run(
    command: str,
    job_name: str = "unnamed",
    retries: int = 0,
    retry_delay: float = 5.0,
    timeout: Optional[int] = None,
    history: Optional[JobHistory] = None,
) -> RunResult:
    """Execute a shell command with optional retry logic and history recording."""
    started_at = datetime.now(timezone.utc)
    attempt = 0
    last_result: Optional[RunResult] = None

    while attempt <= retries:
        attempt += 1
        logger.info("[%s] attempt %d/%d: %s", job_name, attempt, retries + 1, command)

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            logger.error("[%s] timed out after %s seconds", job_name, timeout)
            exit_code = -1
            stdout = ""
            stderr = f"TimeoutExpired: {exc}"

        finished_at = datetime.now(timezone.utc)
        last_result = RunResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            attempts=attempt,
            started_at=started_at,
            finished_at=finished_at,
        )

        if last_result.success:
            logger.info("[%s] succeeded on attempt %d", job_name, attempt)
            break

        logger.warning(
            "[%s] failed (exit %d) on attempt %d", job_name, exit_code, attempt
        )
        if attempt <= retries:
            time.sleep(retry_delay)

    if history is not None and last_result is not None:
        history.record(
            HistoryEntry(
                job_name=job_name,
                command=command,
                started_at=last_result.started_at.isoformat(),
                finished_at=last_result.finished_at.isoformat(),
                exit_code=last_result.exit_code,
                attempts=last_result.attempts,
                stdout=last_result.stdout,
                stderr=last_result.stderr,
            )
        )

    return last_result

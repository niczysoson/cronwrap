"""Core runner for cronwrap — executes commands with retry and alerting support."""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from cronwrap.logger import get_logger
from cronwrap.alerting import AlertConfig, send_failure_alert

logger = get_logger(__name__)


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    attempts: int
    success: bool


def run(
    command: str,
    retries: int = 0,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None,
    alert_config: Optional[AlertConfig] = None,
) -> RunResult:
    """Run a shell command with optional retries and failure alerting."""
    attempts = 0
    last_result = None

    for attempt in range(1, retries + 2):
        attempts = attempt
        logger.info("Running command (attempt %d/%d): %s", attempt, retries + 1, command)

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            logger.error("Command timed out after %s seconds: %s", timeout, command)
            last_result = RunResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"TimeoutExpired: {exc}",
                attempts=attempts,
                success=False,
            )
            if attempt <= retries:
                time.sleep(retry_delay)
            continue

        last_result = RunResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            attempts=attempts,
            success=proc.returncode == 0,
        )

        if last_result.success:
            logger.info("Command succeeded on attempt %d: %s", attempt, command)
            return last_result

        logger.warning(
            "Command failed (attempt %d/%d) with code %d: %s",
            attempt, retries + 1, proc.returncode, command,
        )
        if proc.stderr:
            logger.debug("stderr: %s", proc.stderr.strip())

        if attempt <= retries:
            logger.info("Retrying in %.1f seconds...", retry_delay)
            time.sleep(retry_delay)

    # All attempts exhausted
    if last_result and not last_result.success:
        logger.error(
            "Command failed after %d attempt(s): %s", attempts, command
        )
        if alert_config is not None:
            sent = send_failure_alert(
                alert_config,
                command,
                last_result.returncode,
                last_result.stdout,
                last_result.stderr,
                attempts,
            )
            if sent:
                logger.info("Failure alert sent for command: %s", command)
            else:
                logger.warning("Failed to send alert for command: %s", command)

    return last_result

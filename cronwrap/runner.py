import subprocess
import time
import logging
from typing import Optional, List
from .logger import get_logger


def run(
    command: List[str],
    retries: int = 0,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None,
    job_name: str = "cron_job",
) -> int:
    """
    Run a command with optional retry logic and logging.

    Args:
        command: Command and arguments to execute.
        retries: Number of times to retry on failure.
        retry_delay: Seconds to wait between retries.
        timeout: Optional timeout in seconds.
        job_name: Identifier used in log messages.

    Returns:
        Exit code of the command.
    """
    logger = get_logger(job_name)
    attempts = retries + 1

    for attempt in range(1, attempts + 1):
        logger.info("Starting attempt %d/%d: %s", attempt, attempts, " ".join(command))
        start = time.monotonic()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.monotonic() - start
            logger.info("Finished in %.2fs with exit code %d", elapsed, result.returncode)

            if result.stdout:
                logger.debug("stdout:\n%s", result.stdout.rstrip())
            if result.stderr:
                logger.warning("stderr:\n%s", result.stderr.rstrip())

            if result.returncode == 0:
                return result.returncode

            logger.error("Command failed with exit code %d", result.returncode)

        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            logger.error("Command timed out after %.2fs", elapsed)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error: %s", exc)

        if attempt < attempts:
            logger.info("Retrying in %.1f seconds...", retry_delay)
            time.sleep(retry_delay)

    logger.error("All %d attempt(s) failed for job '%s'", attempts, job_name)
    return 1

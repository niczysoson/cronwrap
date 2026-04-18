"""Simple file-based locking to prevent overlapping cron job executions."""

import os
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_LOCK_DIR = "/tmp/cronwrap/locks"


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


class JobLock:
    """File-based lock for a named cron job.

    Creates a lock file containing the current PID. If the lock file exists
    and the recorded PID is still running, acquisition fails. Stale locks
    (PID no longer alive) are automatically removed.
    """

    def __init__(self, job_name: str, lock_dir: str = DEFAULT_LOCK_DIR):
        self.job_name = job_name
        self.lock_dir = Path(lock_dir)
        self.lock_file = self.lock_dir / f"{job_name}.lock"
        self._acquired = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire(self) -> None:
        """Acquire the lock or raise LockError if already held."""
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        if self.lock_file.exists():
            existing_pid = self._read_pid()
            if existing_pid is not None and _pid_alive(existing_pid):
                raise LockError(
                    f"Job '{self.job_name}' is already running (PID {existing_pid})"
                )
            # Stale lock — remove it
            logger.warning(
                "Removing stale lock for '%s' (PID %s no longer alive)",
                self.job_name,
                existing_pid,
            )
            self.lock_file.unlink(missing_ok=True)

        self.lock_file.write_text(str(os.getpid()))
        self._acquired = True
        logger.debug("Lock acquired for '%s' (PID %d)", self.job_name, os.getpid())

    def release(self) -> None:
        """Release the lock if it was acquired by this process."""
        if not self._acquired:
            return
        try:
            self.lock_file.unlink(missing_ok=True)
            self._acquired = False
            logger.debug("Lock released for '%s'", self.job_name)
        except OSError as exc:
            logger.warning("Failed to release lock for '%s': %s", self.job_name, exc)

    def is_locked(self) -> bool:
        """Return True if the job appears to be running right now."""
        if not self.lock_file.exists():
            return False
        pid = self._read_pid()
        return pid is not None and _pid_alive(pid)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "JobLock":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_pid(self) -> Optional[int]:
        try:
            return int(self.lock_file.read_text().strip())
        except (ValueError, OSError):
            return None


def _pid_alive(pid: int) -> bool:
    """Return True if a process with *pid* is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it — treat as alive
        return True

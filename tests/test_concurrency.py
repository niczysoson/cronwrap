"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import os
import pytest
from pathlib import Path

from cronwrap.concurrency import (
    ConcurrencyConfig,
    ConcurrencyError,
    concurrency_from_dict,
    acquire_slot,
    release_slot,
    current_count,
)


@pytest.fixture()
def lock_dir(tmp_path: Path) -> str:
    return str(tmp_path / "locks")


def _cfg(lock_dir: str, max_concurrent: int = 1) -> ConcurrencyConfig:
    return ConcurrencyConfig(max_concurrent=max_concurrent, lock_dir=lock_dir)


def test_config_valid(lock_dir):
    cfg = _cfg(lock_dir, max_concurrent=3)
    assert cfg.max_concurrent == 3


def test_config_invalid(lock_dir):
    with pytest.raises(ValueError):
        ConcurrencyConfig(max_concurrent=0, lock_dir=lock_dir)


def test_concurrency_from_dict(lock_dir):
    cfg = concurrency_from_dict({"max_concurrent": 2, "lock_dir": lock_dir})
    assert cfg.max_concurrent == 2


def test_acquire_and_release(lock_dir):
    cfg = _cfg(lock_dir)
    slot = acquire_slot("myjob", cfg)
    assert os.path.exists(slot)
    assert current_count("myjob", cfg) == 1
    release_slot(slot)
    assert current_count("myjob", cfg) == 0


def test_limit_exceeded(lock_dir):
    cfg = _cfg(lock_dir, max_concurrent=1)
    slot = acquire_slot("myjob", cfg)
    try:
        with pytest.raises(ConcurrencyError):
            acquire_slot("myjob", cfg)
    finally:
        release_slot(slot)


def test_multiple_slots_allowed(lock_dir):
    cfg = _cfg(lock_dir, max_concurrent=3)
    slots = [acquire_slot("myjob", cfg) for _ in range(3)]
    assert current_count("myjob", cfg) == 3
    with pytest.raises(ConcurrencyError):
        acquire_slot("myjob", cfg)
    for s in slots:
        release_slot(s)


def test_release_missing_slot_is_noop(lock_dir):
    release_slot("/tmp/cronwrap_concurrency/nonexistent.lock")  # should not raise


def test_different_jobs_independent(lock_dir):
    cfg = _cfg(lock_dir, max_concurrent=1)
    s1 = acquire_slot("job_a", cfg)
    s2 = acquire_slot("job_b", cfg)  # different job — should succeed
    assert current_count("job_a", cfg) == 1
    assert current_count("job_b", cfg) == 1
    release_slot(s1)
    release_slot(s2)

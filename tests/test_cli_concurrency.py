"""Tests for cronwrap.cli_concurrency."""
from __future__ import annotations

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from cronwrap.concurrency import ConcurrencyConfig, acquire_slot, release_slot
from cronwrap.cli_concurrency import render_concurrency_status, check_and_exit_if_at_limit


@pytest.fixture()
def cfg(tmp_path: Path) -> ConcurrencyConfig:
    return ConcurrencyConfig(max_concurrent=2, lock_dir=str(tmp_path / "locks"))


def test_render_no_active(cfg):
    out = render_concurrency_status("myjob", cfg)
    assert "2" in out
    assert "0" in out  # active


def test_render_with_active(cfg):
    slot = acquire_slot("myjob", cfg)
    try:
        out = render_concurrency_status("myjob", cfg)
        assert "1" in out
    finally:
        release_slot(slot)


def test_check_acquires_slot(cfg):
    slot = check_and_exit_if_at_limit("myjob", cfg)
    assert slot is not None
    assert os.path.exists(slot)
    release_slot(slot)


def test_check_exits_when_limit_reached(cfg):
    slot = acquire_slot("myjob", cfg)
    acquire_slot("myjob", cfg)  # fills both slots
    try:
        with pytest.raises(SystemExit) as exc_info:
            check_and_exit_if_at_limit("myjob", cfg)
        assert exc_info.value.code == 75
    finally:
        # clean up all slots
        from cronwrap.concurrency import _slot_paths
        for p in _slot_paths("myjob", cfg.lock_dir):
            release_slot(p)

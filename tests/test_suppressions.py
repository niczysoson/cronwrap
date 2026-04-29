"""Tests for cronwrap.suppressions and cronwrap.cli_suppressions."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.suppressions import SuppressionRule, SuppressionStore
from cronwrap.cli_suppressions import (
    render_suppression_list,
    check_and_exit_if_suppressed,
)

UTC = timezone.utc
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _rule(job: str = "backup", offset_hours: int = 2, reason: str = "maintenance") -> SuppressionRule:
    return SuppressionRule(
        job_name=job,
        reason=reason,
        expires_at=_NOW + timedelta(hours=offset_hours),
        created_at=_NOW,
    )


@pytest.fixture()
def store_path(tmp_path: Path) -> str:
    return str(tmp_path / "suppressions.json")


# --- SuppressionRule ---

def test_rule_is_active_before_expiry():
    r = _rule(offset_hours=1)
    assert r.is_active(_NOW)


def test_rule_is_inactive_after_expiry():
    r = _rule(offset_hours=-1)
    assert not r.is_active(_NOW)


def test_rule_round_trip():
    r = _rule()
    assert SuppressionRule.from_dict(r.to_dict()).job_name == r.job_name
    assert SuppressionRule.from_dict(r.to_dict()).reason == r.reason


# --- SuppressionStore ---

def test_empty_store_not_suppressed(store_path):
    s = SuppressionStore(store_path)
    assert not s.is_suppressed("backup", _NOW)


def test_add_and_is_suppressed(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("backup"))
    assert s.is_suppressed("backup", _NOW)


def test_other_job_not_suppressed(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("backup"))
    assert not s.is_suppressed("cleanup", _NOW)


def test_expired_rule_not_suppressed(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("backup", offset_hours=-1))
    assert not s.is_suppressed("backup", _NOW)


def test_remove_expired_cleans_up(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("backup", offset_hours=-1))
    s.add(_rule("cleanup", offset_hours=2))
    removed = s.remove_expired(_NOW)
    assert removed == 1
    assert not s.is_suppressed("backup", _NOW)
    assert s.is_suppressed("cleanup", _NOW)


def test_all_active_returns_only_active(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("a", offset_hours=1))
    s.add(_rule("b", offset_hours=-1))
    active = s.all_active(_NOW)
    assert len(active) == 1
    assert active[0].job_name == "a"


# --- CLI helpers ---

def test_render_empty_list():
    output = render_suppression_list([], _NOW)
    assert "No active suppressions" in output


def test_render_with_rules():
    rules = [_rule("backup", reason="planned maintenance")]
    output = render_suppression_list(rules, _NOW)
    assert "backup" in output
    assert "planned maintenance" in output


def test_check_and_exit_if_suppressed_exits(store_path):
    s = SuppressionStore(store_path)
    s.add(_rule("backup"))
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_suppressed(s, "backup", _NOW)
    assert exc.value.code == 0


def test_check_and_exit_if_not_suppressed_passes(store_path):
    s = SuppressionStore(store_path)
    # Should not raise
    check_and_exit_if_suppressed(s, "backup", _NOW)

"""Tests for cronwrap.escalation and cronwrap.cli_escalation."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from cronwrap.escalation import (
    EscalationConfig,
    EscalationResult,
    check_escalation,
    count_consecutive_failures,
    escalation_from_dict,
)
from cronwrap.cli_escalation import render_escalation_config, render_escalation_result
from cronwrap.history import HistoryEntry


def _entry(job: str, success: bool, ts: float = 1_000_000.0) -> HistoryEntry:
    return HistoryEntry(
        job_name=job,
        command="echo hi",
        started_at=ts,
        finished_at=ts + 1.0,
        exit_code=0 if success else 1,
        stdout="",
        stderr="",
    )


def _store(entries):
    store = MagicMock()
    store.for_job = MagicMock(return_value=entries)
    return store


# --- EscalationConfig ---

def test_config_valid():
    cfg = EscalationConfig(threshold=2, channels=["slack"], cooldown_seconds=60)
    assert cfg.threshold == 2
    assert cfg.channels == ["slack"]


def test_config_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        EscalationConfig(threshold=0)


def test_config_invalid_cooldown():
    with pytest.raises(ValueError, match="cooldown"):
        EscalationConfig(cooldown_seconds=-1)


def test_escalation_from_dict():
    cfg = escalation_from_dict({"threshold": 5, "channels": ["pagerduty"], "cooldown_seconds": 300})
    assert cfg.threshold == 5
    assert cfg.channels == ["pagerduty"]
    assert cfg.cooldown_seconds == 300


def test_escalation_from_dict_defaults():
    cfg = escalation_from_dict({})
    assert cfg.enabled is True
    assert cfg.threshold == 3
    assert cfg.channels == []


# --- count_consecutive_failures ---

def test_no_failures_returns_zero():
    store = _store([_entry("j", True), _entry("j", True)])
    assert count_consecutive_failures("j", store) == 0


def test_all_failures():
    store = _store([_entry("j", False), _entry("j", False), _entry("j", False)])
    assert count_consecutive_failures("j", store) == 3


def test_trailing_failures_only():
    store = _store([_entry("j", True), _entry("j", False), _entry("j", False)])
    assert count_consecutive_failures("j", store) == 2


# --- check_escalation ---

def test_disabled_never_escalates():
    cfg = EscalationConfig(enabled=False, threshold=1, channels=["slack"])
    store = _store([_entry("j", False)] * 5)
    result = check_escalation("j", cfg, store)
    assert not result.should_escalate


def test_below_threshold_no_escalation():
    cfg = EscalationConfig(threshold=3, channels=["slack"])
    store = _store([_entry("j", False), _entry("j", False)])
    result = check_escalation("j", cfg, store)
    assert not result.should_escalate
    assert result.consecutive_failures == 2


def test_at_threshold_escalates():
    cfg = EscalationConfig(threshold=3, channels=["slack", "email"])
    store = _store([_entry("j", False)] * 3)
    result = check_escalation("j", cfg, store)
    assert result.should_escalate
    assert result.channels == ["slack", "email"]


def test_cooldown_suppresses_repeat_escalation():
    cfg = EscalationConfig(threshold=2, channels=["slack"], cooldown_seconds=300)
    store = _store([_entry("j", False)] * 4)
    result = check_escalation("j", cfg, store, last_escalation_ts=1_000_000.0, now_ts=1_000_100.0)
    assert not result.should_escalate
    assert "cooldown" in result.reason


def test_cooldown_expired_allows_escalation():
    cfg = EscalationConfig(threshold=2, channels=["slack"], cooldown_seconds=60)
    store = _store([_entry("j", False)] * 4)
    result = check_escalation("j", cfg, store, last_escalation_ts=1_000_000.0, now_ts=1_000_100.0)
    assert result.should_escalate


# --- rendering ---

def test_render_config_contains_threshold():
    cfg = EscalationConfig(threshold=4, channels=["ops"])
    out = render_escalation_config(cfg)
    assert "4" in out
    assert "ops" in out


def test_render_result_no_escalation():
    result = EscalationResult(False, 1, [], "1 failures < threshold 3")
    out = render_escalation_result(result)
    assert "✓" in out


def test_render_result_escalating():
    result = EscalationResult(True, 3, ["slack"], "threshold reached")
    out = render_escalation_result(result)
    assert "🔺" in out
    assert "slack" in out

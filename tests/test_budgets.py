"""Tests for cronwrap.budgets and cronwrap.cli_budgets."""
from __future__ import annotations

import time
import pytest

from cronwrap.budgets import (
    BudgetConfig,
    BudgetResult,
    BudgetTimer,
    budget_from_dict,
)
from cronwrap.cli_budgets import (
    render_budget_config,
    render_budget_result,
    check_and_exit_if_over_budget,
)


# ---------------------------------------------------------------------------
# BudgetConfig validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = BudgetConfig(max_seconds=60.0, warn_at_seconds=45.0)
    assert cfg.max_seconds == 60.0
    assert cfg.warn_at_seconds == 45.0
    assert cfg.enabled is True


def test_config_invalid_max_seconds():
    with pytest.raises(ValueError, match="max_seconds"):
        BudgetConfig(max_seconds=0)


def test_config_invalid_warn_at_not_positive():
    with pytest.raises(ValueError, match="warn_at_seconds"):
        BudgetConfig(max_seconds=60, warn_at_seconds=0)


def test_config_invalid_warn_at_gte_max():
    with pytest.raises(ValueError, match="warn_at_seconds"):
        BudgetConfig(max_seconds=30, warn_at_seconds=30)


def test_budget_from_dict():
    cfg = budget_from_dict({"max_seconds": "120", "warn_at_seconds": "90", "enabled": False})
    assert cfg.max_seconds == 120.0
    assert cfg.warn_at_seconds == 90.0
    assert cfg.enabled is False


def test_budget_from_dict_defaults():
    cfg = budget_from_dict({"max_seconds": 10})
    assert cfg.warn_at_seconds is None
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# BudgetTimer evaluation
# ---------------------------------------------------------------------------

def test_timer_ok():
    cfg = BudgetConfig(max_seconds=10.0)
    with BudgetTimer(cfg) as timer:
        pass  # near-instant
    result = timer.evaluate()
    assert result.over_budget is False
    assert result.warned is False


def test_timer_over_budget():
    cfg = BudgetConfig(max_seconds=0.05)
    with BudgetTimer(cfg) as timer:
        time.sleep(0.1)
    result = timer.evaluate()
    assert result.over_budget is True
    assert result.warned is False


def test_timer_warns():
    cfg = BudgetConfig(max_seconds=10.0, warn_at_seconds=0.01)
    with BudgetTimer(cfg) as timer:
        time.sleep(0.05)
    result = timer.evaluate()
    assert result.over_budget is False
    assert result.warned is True


def test_timer_disabled():
    cfg = BudgetConfig(max_seconds=0.01, enabled=False)
    with BudgetTimer(cfg) as timer:
        time.sleep(0.05)
    result = timer.evaluate()
    assert result.over_budget is False
    assert result.warned is False


# ---------------------------------------------------------------------------
# BudgetResult.summary
# ---------------------------------------------------------------------------

def _make_result(elapsed, over, warned, max_s=60.0, warn_s=None, enabled=True):
    cfg = BudgetConfig(max_seconds=max_s, warn_at_seconds=warn_s, enabled=enabled)
    return BudgetResult(elapsed_seconds=elapsed, over_budget=over, warned=warned, budget=cfg)


def test_summary_ok():
    r = _make_result(5.0, False, False)
    assert "OK" in r.summary


def test_summary_over():
    r = _make_result(70.0, True, False)
    assert "OVER BUDGET" in r.summary


def test_summary_warn():
    r = _make_result(50.0, False, True, warn_s=45.0)
    assert "WARNING" in r.summary


def test_summary_disabled():
    r = _make_result(5.0, False, False, enabled=False)
    assert "disabled" in r.summary


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_budget_config_includes_max():
    cfg = BudgetConfig(max_seconds=300, warn_at_seconds=240)
    out = render_budget_config(cfg)
    assert "300" in out or "5m" in out
    assert "enabled" in out


def test_render_budget_result_ok():
    r = _make_result(5.0, False, False)
    out = render_budget_result(r)
    assert "OK" in out


def test_render_budget_result_over():
    r = _make_result(70.0, True, False)
    out = render_budget_result(r)
    assert "OVER BUDGET" in out


def test_check_and_exit_if_over_budget_raises(capsys):
    r = _make_result(70.0, True, False)
    with pytest.raises(SystemExit) as exc_info:
        check_and_exit_if_over_budget(r)
    assert exc_info.value.code == 1


def test_check_and_exit_if_over_budget_passes(capsys):
    r = _make_result(5.0, False, False)
    check_and_exit_if_over_budget(r)  # should not raise

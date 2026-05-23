"""Tests for cronwrap.trigger and cronwrap.cli_trigger."""
from __future__ import annotations

import pytest

from cronwrap.trigger import TriggerConfig, trigger_from_dict
from cronwrap.cli_trigger import render_trigger_status, check_and_exit_if_not_triggered


@pytest.fixture()
def cfg(tmp_path):
    return TriggerConfig(state_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# TriggerConfig
# ---------------------------------------------------------------------------

def test_config_defaults():
    c = TriggerConfig(state_dir="/tmp/x")
    assert c.enabled is True


def test_config_invalid_enabled():
    with pytest.raises(ValueError):
        TriggerConfig(enabled="yes", state_dir="/tmp/x")  # type: ignore


def test_config_invalid_state_dir():
    with pytest.raises(ValueError):
        TriggerConfig(state_dir="")


def test_trigger_from_dict():
    c = trigger_from_dict({"enabled": False, "state_dir": "/tmp/t"})
    assert c.enabled is False
    assert c.state_dir == "/tmp/t"


def test_trigger_from_dict_defaults():
    c = trigger_from_dict({})
    assert c.enabled is True


# ---------------------------------------------------------------------------
# set / is / clear
# ---------------------------------------------------------------------------

def test_not_triggered_initially(cfg):
    assert cfg.is_triggered("backup") is False


def test_set_and_is_triggered(cfg):
    cfg.set_trigger("backup")
    assert cfg.is_triggered("backup") is True


def test_clear_removes_trigger(cfg):
    cfg.set_trigger("backup")
    cfg.clear_trigger("backup")
    assert cfg.is_triggered("backup") is False


def test_clear_nonexistent_is_safe(cfg):
    cfg.clear_trigger("nope")  # should not raise


def test_trigger_info_contains_timestamp(cfg):
    cfg.set_trigger("myjob")
    info = cfg.trigger_info("myjob")
    assert info is not None
    assert "triggered_at" in info
    assert info["job"] == "myjob"


def test_trigger_info_missing_returns_none(cfg):
    assert cfg.trigger_info("ghost") is None


def test_disabled_config_never_triggers(tmp_path):
    cfg = TriggerConfig(enabled=False, state_dir=str(tmp_path))
    cfg.set_trigger("job")  # should be a no-op
    assert cfg.is_triggered("job") is False


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_disabled(tmp_path):
    cfg = TriggerConfig(enabled=False, state_dir=str(tmp_path))
    out = render_trigger_status(cfg, "job")
    assert "disabled" in out


def test_render_not_triggered(cfg):
    out = render_trigger_status(cfg, "job")
    assert "no pending" in out


def test_render_triggered(cfg):
    cfg.set_trigger("job")
    out = render_trigger_status(cfg, "job")
    assert "pending" in out
    assert "job" in out


def test_check_no_require_trigger_passes(cfg):
    # Should not raise even without a trigger set
    check_and_exit_if_not_triggered(cfg, "job", require_trigger=False)


def test_check_require_trigger_exits_when_absent(cfg):
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_not_triggered(cfg, "job", require_trigger=True)
    assert exc.value.code == 0


def test_check_require_trigger_passes_when_set(cfg):
    cfg.set_trigger("job")
    check_and_exit_if_not_triggered(cfg, "job", require_trigger=True)  # no raise

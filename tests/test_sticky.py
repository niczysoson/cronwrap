"""Tests for cronwrap.sticky and cronwrap.cli_sticky."""
from __future__ import annotations

import json
import pytest

from cronwrap.sticky import StickyConfig, sticky_from_dict
from cronwrap.cli_sticky import render_sticky_status, check_and_exit_if_sticky


@pytest.fixture()
def cfg(tmp_path):
    return StickyConfig(state_dir=str(tmp_path / "sticky"))


def test_config_defaults():
    c = StickyConfig()
    assert c.enabled is True
    assert c.state_dir == "/tmp/cronwrap/sticky"


def test_config_invalid_enabled():
    with pytest.raises(ValueError):
        StickyConfig(enabled="yes")  # type: ignore[arg-type]


def test_config_invalid_state_dir():
    with pytest.raises(ValueError):
        StickyConfig(state_dir="")


def test_sticky_from_dict():
    c = sticky_from_dict({"enabled": False, "state_dir": "/tmp/x"})
    assert c.enabled is False
    assert c.state_dir == "/tmp/x"


def test_sticky_from_dict_defaults():
    c = sticky_from_dict({})
    assert c.enabled is True


def test_not_sticky_initially(cfg):
    assert cfg.is_sticky("my_job") is False
    assert cfg.state("my_job") is None


def test_mark_failed_sets_sticky(cfg):
    cfg.mark_failed("my_job", exit_code=2)
    assert cfg.is_sticky("my_job") is True
    st = cfg.state("my_job")
    assert st["job"] == "my_job"
    assert st["exit_code"] == 2
    assert "failed_at" in st


def test_clear_removes_sticky(cfg):
    cfg.mark_failed("my_job")
    cfg.clear("my_job")
    assert cfg.is_sticky("my_job") is False


def test_clear_noop_when_not_sticky(cfg):
    cfg.clear("my_job")  # should not raise


def test_disabled_never_sticky(tmp_path):
    cfg = StickyConfig(enabled=False, state_dir=str(tmp_path / "s"))
    cfg.mark_failed("my_job")
    assert cfg.is_sticky("my_job") is False


def test_render_not_sticky(cfg):
    out = render_sticky_status(cfg, "my_job")
    assert "no active failure" in out
    assert "my_job" in out


def test_render_sticky(cfg):
    cfg.mark_failed("my_job", exit_code=3)
    out = render_sticky_status(cfg, "my_job")
    assert "STUCK" in out
    assert "exit_code=3" in out


def test_render_disabled(tmp_path):
    cfg = StickyConfig(enabled=False, state_dir=str(tmp_path))
    out = render_sticky_status(cfg, "my_job")
    assert "disabled" in out


def test_check_exits_when_sticky(cfg):
    cfg.mark_failed("my_job")
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_sticky(cfg, "my_job")
    assert exc.value.code == 1


def test_check_passes_when_not_sticky(cfg):
    check_and_exit_if_sticky(cfg, "my_job")  # should not raise

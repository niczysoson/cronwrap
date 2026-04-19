"""Tests for cronwrap.pinned and cronwrap.cli_pinned."""
import pytest
from unittest.mock import patch

from cronwrap.pinned import PinnedConfig, pinned_from_dict
from cronwrap.cli_pinned import render_pin_status, check_and_exit_if_changed


@pytest.fixture()
def pin_dir(tmp_path):
    return str(tmp_path / "pins")


def _cfg(pin_dir, config=None, enabled=True):
    return PinnedConfig(
        job_name="backup",
        config_dict=config or {"cmd": "pg_dump", "schedule": "0 2 * * *"},
        pin_dir=pin_dir,
        enabled=enabled,
    )


def test_no_saved_pin_not_changed(pin_dir):
    cfg = _cfg(pin_dir)
    assert not cfg.is_changed()


def test_save_and_unchanged(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    assert not cfg.is_changed()


def test_save_then_config_changes(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    cfg.config_dict = {"cmd": "pg_dump", "schedule": "0 3 * * *"}
    assert cfg.is_changed()


def test_clear_removes_pin(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    cfg.clear()
    assert cfg.saved_hash() is None


def test_disabled_never_changed(pin_dir):
    cfg = _cfg(pin_dir, enabled=False)
    cfg.save()
    cfg.config_dict = {"cmd": "something_else"}
    assert not cfg.is_changed()


def test_pinned_from_dict(pin_dir):
    cfg = pinned_from_dict(
        {"job_name": "backup", "config": {"k": "v"}, "pin_dir": pin_dir}
    )
    assert cfg.job_name == "backup"
    assert cfg.enabled is True


def test_invalid_job_name():
    with pytest.raises(ValueError):
        PinnedConfig(job_name="", config_dict={})


def test_render_no_pin(pin_dir):
    cfg = _cfg(pin_dir)
    out = render_pin_status(cfg)
    assert "no pin saved" in out


def test_render_ok(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    assert "OK" in render_pin_status(cfg)


def test_render_changed(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    cfg.config_dict = {"cmd": "new"}
    assert "CHANGED" in render_pin_status(cfg)


def test_check_exits_on_change(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    cfg.config_dict = {"cmd": "new"}
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_changed(cfg)
    assert exc.value.code == 1


def test_check_passes_when_unchanged(pin_dir):
    cfg = _cfg(pin_dir)
    cfg.save()
    check_and_exit_if_changed(cfg)  # should not raise

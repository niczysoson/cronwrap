"""Tests for cronwrap.cli_trigger_cmd."""
from __future__ import annotations

import json
import pytest

from cronwrap.cli_trigger_cmd import cmd_trigger


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def _cfg_arg(state_dir: str, enabled: bool = True) -> str:
    return json.dumps({"state_dir": state_dir, "enabled": enabled})


def test_set_creates_trigger(state_dir, capsys):
    cmd_trigger(["set", "--job", "backup", "--config", _cfg_arg(state_dir)])
    out = capsys.readouterr().out
    assert "trigger set" in out


def test_clear_removes_trigger(state_dir, capsys):
    # Set first, then clear
    cmd_trigger(["set", "--job", "backup", "--config", _cfg_arg(state_dir)])
    cmd_trigger(["clear", "--job", "backup", "--config", _cfg_arg(state_dir)])
    out = capsys.readouterr().out
    assert "cleared" in out


def test_status_no_trigger(state_dir, capsys):
    cmd_trigger(["status", "--job", "backup", "--config", _cfg_arg(state_dir)])
    out = capsys.readouterr().out
    assert "no pending" in out


def test_status_with_trigger(state_dir, capsys):
    cmd_trigger(["set", "--job", "backup", "--config", _cfg_arg(state_dir)])
    capsys.readouterr()  # discard set output
    cmd_trigger(["status", "--job", "backup", "--config", _cfg_arg(state_dir)])
    out = capsys.readouterr().out
    assert "pending" in out


def test_invalid_json_config_exits(state_dir):
    with pytest.raises(SystemExit) as exc:
        cmd_trigger(["set", "--job", "backup", "--config", "{bad json"])
    assert exc.value.code == 1


def test_invalid_config_values_exits(state_dir):
    bad = json.dumps({"state_dir": ""})
    with pytest.raises(SystemExit) as exc:
        cmd_trigger(["set", "--job", "backup", "--config", bad])
    assert exc.value.code == 1

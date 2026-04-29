"""Tests for cronwrap.cli_isolation_cmd."""
import json
import pytest

from cronwrap.cli_isolation_cmd import cmd_isolation


def test_show_default_config(capsys):
    rc = cmd_isolation(["show", "--config", "{}"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "enabled" in out


def test_show_disabled(capsys):
    cfg = json.dumps({"enabled": False})
    rc = cmd_isolation(["show", "--config", cfg])
    out = capsys.readouterr().out
    assert rc == 0
    assert "disabled" in out


def test_show_with_allowlist(capsys):
    cfg = json.dumps({"allowlist": ["HOME", "PATH"]})
    rc = cmd_isolation(["show", "--config", cfg])
    out = capsys.readouterr().out
    assert rc == 0
    assert "HOME" in out


def test_show_invalid_json(capsys):
    rc = cmd_isolation(["show", "--config", "{not json}"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "invalid JSON" in err


def test_show_invalid_config(capsys):
    cfg = json.dumps({"enabled": "yes"})
    rc = cmd_isolation(["show", "--config", cfg])
    err = capsys.readouterr().err
    assert rc == 2
    assert "ERROR" in err


def test_preview_returns_env(capsys, monkeypatch):
    monkeypatch.setenv("_CW_PREVIEW_TEST", "42")
    cfg = json.dumps({"allowlist": ["_CW_PREVIEW_TEST"]})
    rc = cmd_isolation(["preview", "--config", cfg])
    out = capsys.readouterr().out
    assert rc == 0
    assert "_CW_PREVIEW_TEST=42" in out


def test_preview_invalid_json(capsys):
    rc = cmd_isolation(["preview", "--config", "!!!"])
    err = capsys.readouterr().err
    assert rc == 2


def test_no_subcmd_prints_help(capsys):
    rc = cmd_isolation([])
    assert rc == 0

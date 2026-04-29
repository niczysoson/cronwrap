"""Tests for cronwrap.isolation and cronwrap.cli_isolation."""
import os
import pytest

from cronwrap.isolation import IsolationConfig, isolation_from_dict
from cronwrap.cli_isolation import render_isolation_config, summarise_env


# ---------------------------------------------------------------------------
# IsolationConfig construction
# ---------------------------------------------------------------------------

def test_default_config_passes_full_env():
    cfg = IsolationConfig()
    base = {"HOME": "/root", "PATH": "/usr/bin", "SECRET": "abc"}
    env = cfg.build_env(base)
    assert env == base


def test_disabled_config_passes_full_env():
    cfg = IsolationConfig(enabled=False)
    base = {"HOME": "/root", "SECRET": "abc"}
    env = cfg.build_env(base)
    assert env == base


def test_allowlist_filters_env():
    cfg = IsolationConfig(allowlist=["HOME", "PATH"])
    base = {"HOME": "/root", "PATH": "/usr/bin", "SECRET": "abc"}
    env = cfg.build_env(base)
    assert set(env.keys()) == {"HOME", "PATH"}


def test_denylist_strips_keys():
    cfg = IsolationConfig(denylist=["SECRET"])
    base = {"HOME": "/root", "PATH": "/usr/bin", "SECRET": "abc"}
    env = cfg.build_env(base)
    assert "SECRET" not in env
    assert "HOME" in env


def test_allowlist_and_denylist_combined():
    cfg = IsolationConfig(allowlist=["HOME", "SECRET"], denylist=["SECRET"])
    base = {"HOME": "/root", "SECRET": "abc", "PATH": "/usr/bin"}
    env = cfg.build_env(base)
    assert set(env.keys()) == {"HOME"}


def test_inject_adds_keys():
    cfg = IsolationConfig(inject={"JOB_ID": "42"})
    base = {"HOME": "/root"}
    env = cfg.build_env(base)
    assert env["JOB_ID"] == "42"
    assert env["HOME"] == "/root"


def test_inject_overrides_existing():
    cfg = IsolationConfig(inject={"HOME": "/override"})
    base = {"HOME": "/root"}
    env = cfg.build_env(base)
    assert env["HOME"] == "/override"


def test_build_env_uses_os_environ_when_no_base(monkeypatch):
    monkeypatch.setenv("_CW_TEST_VAR", "hello")
    cfg = IsolationConfig()
    env = cfg.build_env()
    assert env["_CW_TEST_VAR"] == "hello"


def test_invalid_enabled_type():
    with pytest.raises(ValueError, match="enabled"):
        IsolationConfig(enabled="yes")  # type: ignore


def test_invalid_allowlist_type():
    with pytest.raises(ValueError, match="allowlist"):
        IsolationConfig(allowlist="HOME")  # type: ignore


# ---------------------------------------------------------------------------
# isolation_from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = isolation_from_dict({})
    assert cfg.enabled is True
    assert cfg.allowlist == []
    assert cfg.denylist == []
    assert cfg.inject == {}


def test_from_dict_full():
    cfg = isolation_from_dict({
        "enabled": False,
        "allowlist": ["HOME"],
        "denylist": ["SECRET"],
        "inject": {"X": "1"},
    })
    assert cfg.enabled is False
    assert cfg.allowlist == ["HOME"]
    assert cfg.denylist == ["SECRET"]
    assert cfg.inject == {"X": "1"}


def test_to_dict_round_trip():
    cfg = IsolationConfig(allowlist=["A"], denylist=["B"], inject={"C": "3"})
    d = cfg.to_dict()
    cfg2 = isolation_from_dict(d)
    assert cfg2.allowlist == ["A"]
    assert cfg2.denylist == ["B"]
    assert cfg2.inject == {"C": "3"}


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_disabled():
    cfg = IsolationConfig(enabled=False)
    lines = render_isolation_config(cfg)
    assert any("disabled" in l for l in lines)
    assert len(lines) == 1


def test_render_enabled_default():
    cfg = IsolationConfig()
    lines = render_isolation_config(cfg)
    assert any("enabled" in l for l in lines)
    assert any("all variables" in l for l in lines)
    assert any("none" in l for l in lines)


def test_render_with_allowlist_and_inject():
    cfg = IsolationConfig(allowlist=["HOME"], inject={"JOB": "x"})
    lines = render_isolation_config(cfg)
    assert any("HOME" in l for l in lines)
    assert any("JOB=x" in l for l in lines)


def test_summarise_env_short():
    env = {"A": "1", "B": "2"}
    s = summarise_env(env)
    assert "2 variable" in s


def test_summarise_env_long():
    env = {str(i): str(i) for i in range(10)}
    s = summarise_env(env)
    assert "..." in s

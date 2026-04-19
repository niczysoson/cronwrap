"""Tests for cronwrap.precheck and cronwrap.cli_precheck."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from cronwrap.precheck import (
    PrecheckConfig,
    precheck_from_dict,
    run_prechecks,
)
from cronwrap.cli_precheck import render_precheck_status, check_and_exit_if_failed


def test_config_valid():
    cfg = PrecheckConfig(required_commands=["python"], min_disk_mb=10)
    assert cfg.min_disk_mb == 10


def test_config_invalid_disk():
    with pytest.raises(ValueError):
        PrecheckConfig(min_disk_mb=-1)


def test_precheck_from_dict():
    cfg = precheck_from_dict({"required_commands": ["ls"], "min_disk_mb": 5})
    assert cfg.required_commands == ["ls"]
    assert cfg.min_disk_mb == 5


def test_passes_when_command_exists():
    cfg = PrecheckConfig(required_commands=["python"])
    result = run_prechecks(cfg)
    assert result.passed
    assert result.failures == []


def test_fails_when_command_missing():
    cfg = PrecheckConfig(required_commands=["__no_such_binary_xyz__"])
    result = run_prechecks(cfg)
    assert not result.passed
    assert any("__no_such_binary_xyz__" in f for f in result.failures)


def test_fails_when_env_var_missing():
    var = "__CRONWRAP_TEST_VAR_MISSING__"
    os.environ.pop(var, None)
    cfg = PrecheckConfig(required_env=[var])
    result = run_prechecks(cfg)
    assert not result.passed
    assert any(var in f for f in result.failures)


def test_passes_when_env_var_set():
    var = "__CRONWRAP_TEST_VAR_SET__"
    os.environ[var] = "yes"
    try:
        cfg = PrecheckConfig(required_env=[var])
        result = run_prechecks(cfg)
        assert result.passed
    finally:
        del os.environ[var]


def test_fails_when_disk_insufficient():
    cfg = PrecheckConfig(min_disk_mb=999_999_999)
    result = run_prechecks(cfg)
    assert not result.passed
    assert any("disk" in f for f in result.failures)


def test_render_shows_failures():
    cfg = PrecheckConfig(required_commands=["__missing__"])
    result = run_prechecks(cfg)
    output = render_precheck_status(cfg, result)
    assert "✗" in output
    assert "__missing__" in output


def test_render_shows_pass():
    cfg = PrecheckConfig()
    result = run_prechecks(cfg)
    output = render_precheck_status(cfg, result)
    assert "✓" in output


def test_check_and_exit_if_failed_exits(capsys):
    cfg = PrecheckConfig(required_commands=["__no_such_binary_xyz__"])
    with pytest.raises(SystemExit) as exc:
        check_and_exit_if_failed(cfg)
    assert exc.value.code == 1


def test_check_and_exit_if_failed_returns_result():
    cfg = PrecheckConfig()
    result = check_and_exit_if_failed(cfg)
    assert result.passed

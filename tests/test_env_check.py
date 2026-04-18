"""Tests for cronwrap.env_check."""
import os
import pytest
from cronwrap.env_check import check_env, check_env_from_dict, EnvCheckResult


def test_all_present(monkeypatch):
    monkeypatch.setenv("DB_URL", "postgres://localhost/db")
    monkeypatch.setenv("SECRET_KEY", "s3cr3t")
    result = check_env(["DB_URL", "SECRET_KEY"])
    assert result.ok
    assert result.summary() == "All required env vars present."


def test_missing_variable(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    result = check_env(["MISSING_VAR"])
    assert not result.ok
    assert "MISSING_VAR" in result.missing
    assert "Missing" in result.summary()


def test_empty_variable_reported(monkeypatch):
    monkeypatch.setenv("BLANK_VAR", "   ")
    result = check_env(["BLANK_VAR"], allow_empty=False)
    assert not result.ok
    assert "BLANK_VAR" in result.empty
    assert "Empty" in result.summary()


def test_empty_variable_allowed(monkeypatch):
    monkeypatch.setenv("BLANK_VAR", "")
    result = check_env(["BLANK_VAR"], allow_empty=True)
    assert result.ok


def test_mixed_missing_and_empty(monkeypatch):
    monkeypatch.setenv("EMPTY_ONE", "")
    monkeypatch.delenv("GONE_VAR", raising=False)
    result = check_env(["EMPTY_ONE", "GONE_VAR"])
    assert "GONE_VAR" in result.missing
    assert "EMPTY_ONE" in result.empty
    assert not result.ok


def test_from_dict(monkeypatch):
    monkeypatch.setenv("API_KEY", "abc123")
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    cfg = {"required_env": ["API_KEY", "WEBHOOK_URL"]}
    result = check_env_from_dict(cfg)
    assert "WEBHOOK_URL" in result.missing
    assert result.empty == []


def test_from_dict_empty_list():
    result = check_env_from_dict({})
    assert result.ok

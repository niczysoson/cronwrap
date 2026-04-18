"""Tests for cronwrap.secrets."""
import os
import pytest
from cronwrap.secrets import (
    MaskConfig,
    mask_config_from_dict,
    mask_text,
    mask_command,
    mask_output,
)


def test_mask_config_defaults():
    cfg = MaskConfig()
    assert cfg.placeholder == "***"
    assert cfg.patterns == []
    assert cfg.env_vars == []


def test_mask_config_invalid_placeholder():
    with pytest.raises(ValueError):
        MaskConfig(placeholder="")


def test_mask_config_from_dict():
    cfg = mask_config_from_dict({"patterns": [r"\d+"], "placeholder": "<REDACTED>"})
    assert cfg.placeholder == "<REDACTED>"
    assert r"\d+" in cfg.patterns


def test_mask_text_by_pattern():
    cfg = MaskConfig(patterns=[r"password=\S+"])
    result = mask_text("cmd --password=secret123 --verbose", cfg)
    assert "secret123" not in result
    assert "***" in result


def test_mask_text_by_env_var(monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "tok_abc123")
    cfg = MaskConfig(env_vars=["MY_TOKEN"])
    result = mask_text("curl -H 'Authorization: tok_abc123'", cfg)
    assert "tok_abc123" not in result
    assert "***" in result


def test_mask_text_env_var_missing(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    cfg = MaskConfig(env_vars=["MISSING_VAR"])
    text = "nothing to replace"
    assert mask_text(text, cfg) == text


def test_mask_command_none_cfg():
    assert mask_command("echo hello", None) == "echo hello"


def test_mask_output_none_cfg():
    assert mask_output("some output", None) == "some output"


def test_custom_placeholder():
    cfg = MaskConfig(patterns=[r"secret"], placeholder="[HIDDEN]")
    assert mask_text("my secret value", cfg) == "my [HIDDEN] value"


def test_multiple_patterns():
    cfg = MaskConfig(patterns=[r"tok_\w+", r"key_\w+"])
    text = "token=tok_abc key=key_xyz other"
    result = mask_text(text, cfg)
    assert "tok_abc" not in result
    assert "key_xyz" not in result

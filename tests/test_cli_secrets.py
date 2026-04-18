"""Tests for cronwrap.cli_secrets."""
from cronwrap.secrets import MaskConfig
from cronwrap.cli_secrets import render_mask_config, apply_mask_to_result
import os


def test_render_disabled():
    out = render_mask_config(None)
    assert "disabled" in out


def test_render_enabled_no_patterns():
    cfg = MaskConfig()
    out = render_mask_config(cfg)
    assert "enabled" in out
    assert "none" in out


def test_render_with_patterns():
    cfg = MaskConfig(patterns=[r"tok_\w+"], env_vars=["API_KEY"])
    out = render_mask_config(cfg)
    assert r"tok_\w+" in out
    assert "API_KEY" in out
    assert "***" in out


def test_render_custom_placeholder():
    cfg = MaskConfig(placeholder="<X>")
    out = render_mask_config(cfg)
    assert "<X>" in out


def test_apply_mask_to_result_none():
    so, se = apply_mask_to_result("hello", "world", None)
    assert so == "hello"
    assert se == "world"


def test_apply_mask_to_result_masks(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s3cr3t")
    cfg = MaskConfig(env_vars=["SECRET_KEY"])
    so, se = apply_mask_to_result("output s3cr3t here", "error s3cr3t here", cfg)
    assert "s3cr3t" not in so
    assert "s3cr3t" not in se

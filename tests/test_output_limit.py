"""Tests for cronwrap.output_limit."""
import pytest
from cronwrap.output_limit import (
    OutputLimitConfig,
    output_limit_from_dict,
    apply_output_limit,
)


def test_default_config_accepts_short_text():
    cfg = OutputLimitConfig()
    text = "hello world"
    assert cfg.apply(text) == text


def test_is_limited_false_for_short_text():
    cfg = OutputLimitConfig(max_bytes=100)
    assert cfg.is_limited("hi") is False


def test_is_limited_true_for_long_text():
    cfg = OutputLimitConfig(max_bytes=5)
    assert cfg.is_limited("hello world") is True


def test_apply_truncates_long_text():
    cfg = OutputLimitConfig(max_bytes=5, truncation_notice="[cut]")
    result = cfg.apply("hello world")
    assert result == "hello[cut]"


def test_apply_preserves_exact_boundary():
    cfg = OutputLimitConfig(max_bytes=5, truncation_notice="[cut]")
    result = cfg.apply("hello")
    assert result == "hello"


def test_invalid_max_bytes_raises():
    with pytest.raises(ValueError):
        OutputLimitConfig(max_bytes=0)


def test_output_limit_from_dict_defaults():
    cfg = output_limit_from_dict({})
    assert cfg.max_bytes == 64 * 1024


def test_output_limit_from_dict_custom():
    cfg = output_limit_from_dict({"max_bytes": 256, "truncation_notice": "..."})
    assert cfg.max_bytes == 256
    assert cfg.truncation_notice == "..."


def test_apply_output_limit_none_cfg():
    text = "x" * 200
    assert apply_output_limit(text, None) == text


def test_apply_output_limit_with_cfg():
    cfg = OutputLimitConfig(max_bytes=3, truncation_notice="!")
    assert apply_output_limit("abcdef", cfg) == "abc!"

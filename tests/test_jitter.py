"""Tests for cronwrap.jitter and cronwrap.cli_jitter."""
import pytest
from unittest.mock import patch
from cronwrap.jitter import JitterConfig, jitter_from_dict, render_jitter
from cronwrap.cli_jitter import render_jitter_status, check_and_apply_jitter


def test_delay_within_bounds():
    cfg = JitterConfig(max_seconds=10)
    for _ in range(20):
        d = cfg.delay()
        assert 0.0 <= d <= 10.0


def test_delay_disabled_returns_zero():
    cfg = JitterConfig(enabled=False, max_seconds=60)
    assert cfg.delay() == 0.0


def test_delay_max_zero_returns_zero():
    cfg = JitterConfig(max_seconds=0)
    assert cfg.delay() == 0.0


def test_invalid_max_seconds():
    with pytest.raises(ValueError):
        JitterConfig(max_seconds=-1)


def test_seed_deterministic():
    a = JitterConfig(max_seconds=100, seed=42)
    b = JitterConfig(max_seconds=100, seed=42)
    assert a.delay() == b.delay()


def test_to_dict():
    cfg = JitterConfig(enabled=True, max_seconds=15)
    d = cfg.to_dict()
    assert d == {"enabled": True, "max_seconds": 15}


def test_from_dict():
    cfg = jitter_from_dict({"enabled": False, "max_seconds": 5})
    assert not cfg.enabled
    assert cfg.max_seconds == 5


def test_from_dict_defaults():
    cfg = jitter_from_dict({})
    assert cfg.enabled is True
    assert cfg.max_seconds == 30


def test_render_jitter_disabled():
    cfg = JitterConfig(enabled=False)
    assert "disabled" in render_jitter(cfg)


def test_render_jitter_enabled():
    cfg = JitterConfig(max_seconds=20)
    out = render_jitter(cfg)
    assert "20" in out and "enabled" in out


def test_render_jitter_status_contains_samples():
    cfg = JitterConfig(max_seconds=10)
    out = render_jitter_status(cfg)
    assert "sample" in out


def test_render_jitter_status_disabled_no_samples():
    cfg = JitterConfig(enabled=False)
    out = render_jitter_status(cfg)
    assert "sample" not in out


def test_check_and_apply_jitter_dry_run():
    cfg = JitterConfig(max_seconds=30, seed=1)
    with patch("time.sleep") as mock_sleep:
        delay = check_and_apply_jitter(cfg, dry_run=True)
        mock_sleep.assert_not_called()
    assert delay >= 0


def test_check_and_apply_jitter_sleeps():
    cfg = JitterConfig(max_seconds=5, seed=7)
    with patch("time.sleep") as mock_sleep:
        delay = check_and_apply_jitter(cfg, dry_run=False)
        if delay > 0:
            mock_sleep.assert_called_once()

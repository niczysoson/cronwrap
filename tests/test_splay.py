"""Tests for cronwrap.splay."""
import pytest
from unittest.mock import patch

from cronwrap.splay import SplayConfig, splay_from_dict, render_splay_status


def test_delay_within_bounds():
    cfg = SplayConfig(max_seconds=10, seed=42)
    for _ in range(50):
        d = cfg.delay()
        assert 0.0 <= d <= 10.0


def test_delay_disabled_returns_zero():
    cfg = SplayConfig(max_seconds=30, enabled=False)
    assert cfg.delay() == 0.0


def test_delay_max_zero_returns_zero():
    cfg = SplayConfig(max_seconds=0)
    assert cfg.delay() == 0.0


def test_invalid_max_seconds():
    with pytest.raises(ValueError):
        SplayConfig(max_seconds=-1)


def test_seed_deterministic():
    cfg1 = SplayConfig(max_seconds=100, seed=7)
    cfg2 = SplayConfig(max_seconds=100, seed=7)
    assert cfg1.delay() == cfg2.delay()


def test_sleep_calls_time_sleep():
    cfg = SplayConfig(max_seconds=5, seed=0)
    expected = cfg.delay()  # consume one value
    cfg2 = SplayConfig(max_seconds=5, seed=0)
    with patch("cronwrap.splay.time.sleep") as mock_sleep:
        slept = cfg2.sleep()
        if slept > 0:
            mock_sleep.assert_called_once_with(slept)


def test_sleep_disabled_does_not_sleep():
    cfg = SplayConfig(max_seconds=60, enabled=False)
    with patch("cronwrap.splay.time.sleep") as mock_sleep:
        result = cfg.sleep()
        mock_sleep.assert_not_called()
        assert result == 0.0


def test_to_dict():
    cfg = SplayConfig(max_seconds=15, enabled=True, seed=3)
    d = cfg.to_dict()
    assert d == {"max_seconds": 15, "enabled": True, "seed": 3}


def test_splay_from_dict():
    cfg = splay_from_dict({"max_seconds": 20, "enabled": False, "seed": 1})
    assert cfg.max_seconds == 20
    assert cfg.enabled is False
    assert cfg.seed == 1


def test_splay_from_dict_defaults():
    cfg = splay_from_dict({})
    assert cfg.max_seconds == 0
    assert cfg.enabled is True
    assert cfg.seed is None


def test_render_disabled():
    cfg = SplayConfig(max_seconds=0)
    assert render_splay_status(cfg) == "splay: disabled"


def test_render_enabled():
    cfg = SplayConfig(max_seconds=30)
    assert render_splay_status(cfg) == "splay: up to 30s random delay before start"

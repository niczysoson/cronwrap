"""Tests for cronwrap.stagger and cronwrap.cli_stagger."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from cronwrap.stagger import StaggerConfig, stagger_from_dict
from cronwrap.cli_stagger import render_stagger_status, check_and_apply_stagger


# ---------------------------------------------------------------------------
# StaggerConfig unit tests
# ---------------------------------------------------------------------------

def test_delay_within_bounds():
    cfg = StaggerConfig(window_seconds=120, seed="my-job")
    d = cfg.delay()
    assert 0.0 <= d < 120.0


def test_delay_disabled_returns_zero():
    cfg = StaggerConfig(enabled=False, window_seconds=60, seed="my-job")
    assert cfg.delay() == 0.0


def test_delay_zero_window_returns_zero():
    # window_seconds=0 is invalid at construction; test via direct attr override
    cfg = StaggerConfig(enabled=True, window_seconds=60, seed="x")
    cfg.window_seconds = 0
    assert cfg.delay() == 0.0


def test_seed_deterministic():
    cfg1 = StaggerConfig(window_seconds=300, seed="backup-job")
    cfg2 = StaggerConfig(window_seconds=300, seed="backup-job")
    assert cfg1.delay() == cfg2.delay()


def test_different_seeds_differ():
    cfg1 = StaggerConfig(window_seconds=3600, seed="job-a")
    cfg2 = StaggerConfig(window_seconds=3600, seed="job-b")
    # Very unlikely to collide
    assert cfg1.delay() != cfg2.delay()


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        StaggerConfig(window_seconds=0)


def test_invalid_window_negative_raises():
    with pytest.raises(ValueError):
        StaggerConfig(window_seconds=-5)


def test_to_dict_round_trip():
    cfg = StaggerConfig(enabled=True, window_seconds=90, seed="nightly", sleep_enabled=False)
    d = cfg.to_dict()
    assert d["window_seconds"] == 90
    assert d["seed"] == "nightly"
    assert d["sleep_enabled"] is False


def test_stagger_from_dict_defaults():
    cfg = stagger_from_dict({})
    assert cfg.enabled is True
    assert cfg.window_seconds == 60
    assert cfg.seed == ""
    assert cfg.sleep_enabled is True


def test_stagger_from_dict_custom():
    cfg = stagger_from_dict({"window_seconds": 30, "seed": "etl", "enabled": False})
    assert cfg.window_seconds == 30
    assert cfg.seed == "etl"
    assert cfg.enabled is False


def test_sleep_calls_time_sleep():
    cfg = StaggerConfig(window_seconds=60, seed="sleepy", sleep_enabled=True)
    expected = cfg.delay()
    with patch("cronwrap.stagger.time.sleep") as mock_sleep:
        result = cfg.sleep()
    mock_sleep.assert_called_once_with(expected)
    assert result == expected


def test_sleep_skipped_when_disabled():
    cfg = StaggerConfig(window_seconds=60, seed="sleepy", sleep_enabled=False)
    with patch("cronwrap.stagger.time.sleep") as mock_sleep:
        cfg.sleep()
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_disabled():
    cfg = StaggerConfig(enabled=False)
    out = render_stagger_status(cfg)
    assert "disabled" in out


def test_render_enabled_shows_delay():
    cfg = StaggerConfig(enabled=True, window_seconds=60, seed="demo", sleep_enabled=False)
    out = render_stagger_status(cfg)
    assert "enabled" in out
    assert "Window" in out
    assert "Delay" in out


def test_check_and_apply_stagger_returns_delay():
    cfg = StaggerConfig(window_seconds=60, seed="check", sleep_enabled=False)
    expected = cfg.delay()
    result = check_and_apply_stagger(cfg)
    assert result == expected

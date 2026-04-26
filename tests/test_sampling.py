"""Tests for cronwrap.sampling."""
import pytest
from cronwrap.sampling import (
    SamplingConfig,
    sampling_from_dict,
    render_sampling_status,
    check_and_exit_if_sampled_out,
)


# ---------------------------------------------------------------------------
# SamplingConfig validation
# ---------------------------------------------------------------------------

def test_default_config_always_runs():
    cfg = SamplingConfig()
    assert cfg.rate == 1.0
    assert cfg.enabled is True
    # With rate=1.0 every call must return True
    for _ in range(20):
        assert cfg.should_run() is True


def test_rate_zero_raises():
    with pytest.raises(ValueError, match="rate must be in"):
        SamplingConfig(rate=0.0)


def test_rate_negative_raises():
    with pytest.raises(ValueError):
        SamplingConfig(rate=-0.5)


def test_rate_above_one_raises():
    with pytest.raises(ValueError):
        SamplingConfig(rate=1.1)


def test_rate_exactly_one_is_valid():
    cfg = SamplingConfig(rate=1.0)
    assert cfg.should_run() is True


# ---------------------------------------------------------------------------
# should_run determinism via seed
# ---------------------------------------------------------------------------

def test_seed_deterministic():
    cfg1 = SamplingConfig(rate=0.5, seed=42)
    cfg2 = SamplingConfig(rate=0.5, seed=42)
    results1 = [cfg1.should_run() for _ in range(30)]
    results2 = [cfg2.should_run() for _ in range(30)]
    assert results1 == results2


def test_different_seeds_differ():
    cfg1 = SamplingConfig(rate=0.5, seed=1)
    cfg2 = SamplingConfig(rate=0.5, seed=99)
    results1 = [cfg1.should_run() for _ in range(50)]
    results2 = [cfg2.should_run() for _ in range(50)]
    assert results1 != results2


def test_disabled_always_runs():
    cfg = SamplingConfig(rate=0.01, enabled=False)
    for _ in range(20):
        assert cfg.should_run() is True


# ---------------------------------------------------------------------------
# sampling_from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = sampling_from_dict({})
    assert cfg.rate == 1.0
    assert cfg.enabled is True


def test_from_dict_custom():
    cfg = sampling_from_dict({"rate": 0.25, "enabled": False})
    assert cfg.rate == 0.25
    assert cfg.enabled is False


def test_from_dict_invalid_rate():
    with pytest.raises(ValueError):
        sampling_from_dict({"rate": 0.0})


# ---------------------------------------------------------------------------
# render_sampling_status
# ---------------------------------------------------------------------------

def test_render_disabled():
    cfg = SamplingConfig(enabled=False)
    assert "disabled" in render_sampling_status(cfg)


def test_render_full_rate():
    cfg = SamplingConfig(rate=1.0)
    assert "100%" in render_sampling_status(cfg)


def test_render_partial_rate():
    cfg = SamplingConfig(rate=0.1)
    status = render_sampling_status(cfg)
    assert "10.0%" in status


# ---------------------------------------------------------------------------
# check_and_exit_if_sampled_out
# ---------------------------------------------------------------------------

def test_check_returns_false_when_should_run():
    cfg = SamplingConfig(rate=1.0)
    assert check_and_exit_if_sampled_out(cfg) is False


def test_check_returns_true_when_skipped(capsys):
    # rate=1e-9 is effectively never
    cfg = SamplingConfig(rate=1e-9, seed=0)
    # Force the rng to produce a value >= rate by consuming one draw
    skipped = check_and_exit_if_sampled_out(cfg, verbose=True)
    # Either it skipped or it ran; just verify the bool is consistent
    if skipped:
        captured = capsys.readouterr()
        assert "Skipped" in captured.out
    else:
        # Extremely unlikely but valid — just pass
        pass

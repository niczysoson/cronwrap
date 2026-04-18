"""Tests for cronwrap.backoff."""
import pytest
from cronwrap.backoff import BackoffConfig, backoff_from_dict, render_backoff


def test_fixed_strategy():
    cfg = BackoffConfig(strategy="fixed", base_delay=5.0)
    assert cfg.delay_for(1) == 5.0
    assert cfg.delay_for(3) == 5.0


def test_linear_strategy():
    cfg = BackoffConfig(strategy="linear", base_delay=2.0, max_delay=100.0)
    assert cfg.delay_for(1) == 2.0
    assert cfg.delay_for(3) == 6.0


def test_exponential_strategy():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=2.0, max_delay=100.0)
    assert cfg.delay_for(1) == 1.0
    assert cfg.delay_for(2) == 2.0
    assert cfg.delay_for(4) == 8.0


def test_max_delay_capped():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=2.0, max_delay=5.0)
    assert cfg.delay_for(10) == 5.0


def test_jitter_strategy_within_bounds():
    cfg = BackoffConfig(strategy="jitter", base_delay=1.0, multiplier=2.0, max_delay=50.0)
    for attempt in range(1, 6):
        d = cfg.delay_for(attempt)
        assert 0 <= d <= 50.0


def test_jitter_flag_on_fixed():
    cfg = BackoffConfig(strategy="fixed", base_delay=10.0, jitter=True)
    for _ in range(20):
        d = cfg.delay_for(1)
        assert 0 <= d <= 10.0


def test_invalid_base_delay():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffConfig(base_delay=-1.0)


def test_invalid_max_delay():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffConfig(base_delay=10.0, max_delay=5.0)


def test_invalid_multiplier():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffConfig(multiplier=0.5)


def test_invalid_strategy():
    with pytest.raises(ValueError, match="Unknown strategy"):
        BackoffConfig(strategy="random_walk")


def test_backoff_from_dict():
    cfg = backoff_from_dict({"strategy": "linear", "base_delay": 3, "max_delay": 60, "multiplier": 1.5})
    assert cfg.strategy == "linear"
    assert cfg.base_delay == 3.0
    assert cfg.max_delay == 60.0


def test_backoff_from_dict_defaults():
    cfg = backoff_from_dict({})
    assert cfg.strategy == "fixed"
    assert cfg.base_delay == 1.0


def test_render_backoff():
    cfg = BackoffConfig(strategy="exponential", base_delay=2.0, max_delay=120.0)
    out = render_backoff(cfg)
    assert "exponential" in out
    assert "2.0" in out
    assert "120.0" in out

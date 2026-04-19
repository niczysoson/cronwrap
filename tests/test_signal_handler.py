"""Tests for cronwrap.signal_handler and cronwrap.cli_signal_handler."""

import signal
import pytest

import cronwrap.signal_handler as sh
from cronwrap.signal_handler import SignalHandlerConfig, register, was_signalled, last_signal, reset
from cronwrap.cli_signal_handler import render_signal_config, render_signal_status


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()
    # restore sensible defaults
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def test_config_defaults():
    cfg = SignalHandlerConfig()
    assert signal.SIGTERM in cfg.signals
    assert signal.SIGINT in cfg.signals


def test_config_empty_signals_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        SignalHandlerConfig(signals=[])


def test_was_signalled_initially_false():
    assert not was_signalled()
    assert last_signal() is None


def test_register_and_trigger():
    received = []
    cfg = SignalHandlerConfig(
        signals=[signal.SIGUSR1],
        on_signal=lambda s: received.append(s),
    )
    register(cfg)
    signal.raise_signal(signal.SIGUSR1)
    assert was_signalled()
    assert last_signal() == signal.SIGUSR1
    assert received == [signal.SIGUSR1]


def test_reset_clears_state():
    cfg = SignalHandlerConfig(signals=[signal.SIGUSR1])
    register(cfg)
    signal.raise_signal(signal.SIGUSR1)
    assert was_signalled()
    reset()
    assert not was_signalled()
    assert last_signal() is None


def test_callback_exception_does_not_propagate():
    def bad_cb(s):
        raise RuntimeError("boom")

    cfg = SignalHandlerConfig(signals=[signal.SIGUSR2], on_signal=bad_cb)
    register(cfg)
    # Should not raise
    signal.raise_signal(signal.SIGUSR2)
    assert was_signalled()


def test_render_signal_config():
    cfg = SignalHandlerConfig(signals=[signal.SIGTERM])
    out = render_signal_config(cfg)
    assert "SIGTERM" in out
    assert "Custom callback : no" in out


def test_render_signal_config_with_callback():
    cfg = SignalHandlerConfig(signals=[signal.SIGTERM], on_signal=lambda s: None)
    out = render_signal_config(cfg)
    assert "Custom callback : yes" in out


def test_render_signal_status_none():
    assert render_signal_status([]) == "No signals received."


def test_render_signal_status_with_signals():
    out = render_signal_status([signal.SIGTERM])
    assert "SIGTERM" in out

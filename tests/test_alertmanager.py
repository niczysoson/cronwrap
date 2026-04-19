"""Tests for cronwrap.alertmanager and cronwrap.cli_alertmanager."""
import pytest
from cronwrap.alertmanager import (
    AlertManagerConfig,
    AlertRule,
    dispatch,
    register_channel,
    get_channel,
    _REGISTRY,
)
from cronwrap.cli_alertmanager import render_alert_rules, render_dispatch_result


@pytest.fixture(autouse=True)
def _clear_registry():
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


def _make_config(rules=None):
    return AlertManagerConfig(rules=rules or [])


def test_register_and_get_channel():
    handler = lambda ch, ev, pl: None
    register_channel("slack", handler)
    assert get_channel("slack") is handler


def test_get_missing_channel_returns_none():
    assert get_channel("nonexistent") is None


def test_dispatch_calls_handler():
    calls = []
    register_channel("email", lambda ch, ev, pl: calls.append((ch, ev, pl)))
    rule = AlertRule(channel="email", events=["failure"])
    cfg = AlertManagerConfig(rules=[rule])
    notified = dispatch(cfg, "failure", {"job": "backup", "exit_code": 1})
    assert notified == ["email"]
    assert calls[0] == ("email", "failure", {"job": "backup", "exit_code": 1})


def test_dispatch_skips_wrong_event():
    calls = []
    register_channel("slack", lambda ch, ev, pl: calls.append(ev))
    rule = AlertRule(channel="slack", events=["failure"])
    cfg = AlertManagerConfig(rules=[rule])
    notified = dispatch(cfg, "success", {"exit_code": 0})
    assert notified == []
    assert calls == []


def test_dispatch_skips_disabled_rule():
    calls = []
    register_channel("pager", lambda ch, ev, pl: calls.append(ev))
    rule = AlertRule(channel="pager", events=["failure"], enabled=False)
    cfg = AlertManagerConfig(rules=[rule])
    notified = dispatch(cfg, "failure", {"exit_code": 2})
    assert notified == []


def test_dispatch_respects_min_exit_code():
    calls = []
    register_channel("ops", lambda ch, ev, pl: calls.append(pl))
    rule = AlertRule(channel="ops", events=["failure"], min_exit_code=2)
    cfg = AlertManagerConfig(rules=[rule])
    assert dispatch(cfg, "failure", {"exit_code": 1}) == []
    assert dispatch(cfg, "failure", {"exit_code": 2}) == ["ops"]


def test_dispatch_unregistered_channel_skipped(caplog):
    rule = AlertRule(channel="ghost", events=["failure"])
    cfg = AlertManagerConfig(rules=[rule])
    notified = dispatch(cfg, "failure", {"exit_code": 1})
    assert notified == []


def test_from_dict_parses_rules():
    d = {"rules": [{"channel": "slack", "events": ["failure", "retry"], "min_exit_code": 1}]}
    cfg = AlertManagerConfig.from_dict(d)
    assert len(cfg.rules) == 1
    assert cfg.rules[0].channel == "slack"
    assert "retry" in cfg.rules[0].events


def test_from_dict_empty():
    cfg = AlertManagerConfig.from_dict({})
    assert cfg.rules == []


def test_render_alert_rules_no_rules():
    cfg = _make_config()
    assert "no rules" in render_alert_rules(cfg)


def test_render_alert_rules_with_rules():
    rule = AlertRule(channel="slack", events=["failure"], enabled=True)
    cfg = AlertManagerConfig(rules=[rule])
    out = render_alert_rules(cfg)
    assert "slack" in out
    assert "failure" in out


def test_render_dispatch_result_empty():
    assert "no channels" in render_dispatch_result([])


def test_render_dispatch_result_channels():
    out = render_dispatch_result(["slack", "email"])
    assert "slack" in out
    assert "email" in out

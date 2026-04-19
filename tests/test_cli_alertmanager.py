"""Tests for cronwrap.cli_alertmanager."""
from cronwrap.alertmanager import AlertManagerConfig, AlertRule
from cronwrap.cli_alertmanager import render_alert_rules, render_dispatch_result


def test_render_no_rules():
    cfg = AlertManagerConfig(rules=[])
    out = render_alert_rules(cfg)
    assert "no rules" in out


def test_render_enabled_rule():
    rule = AlertRule(channel="slack", events=["failure"], enabled=True, min_exit_code=1)
    cfg = AlertManagerConfig(rules=[rule])
    out = render_alert_rules(cfg)
    assert "[on ]" in out
    assert "slack" in out
    assert "failure" in out
    assert "min_exit=1" in out


def test_render_disabled_rule():
    rule = AlertRule(channel="pager", events=["retry"], enabled=False)
    cfg = AlertManagerConfig(rules=[rule])
    out = render_alert_rules(cfg)
    assert "[off]" in out
    assert "pager" in out


def test_render_multiple_rules():
    rules = [
        AlertRule(channel="slack", events=["failure"]),
        AlertRule(channel="email", events=["failure", "retry"]),
    ]
    cfg = AlertManagerConfig(rules=rules)
    out = render_alert_rules(cfg)
    assert "slack" in out
    assert "email" in out


def test_render_dispatch_empty():
    out = render_dispatch_result([])
    assert "no channels" in out


def test_render_dispatch_single():
    out = render_dispatch_result(["slack"])
    assert "slack" in out


def test_render_dispatch_multiple():
    out = render_dispatch_result(["slack", "email", "pager"])
    assert "slack" in out
    assert "email" in out
    assert "pager" in out

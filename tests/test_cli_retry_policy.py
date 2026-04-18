"""Tests for cronwrap.cli_retry_policy."""
from cronwrap.retry_policy import RetryPolicy
from cronwrap.cli_retry_policy import render_retry_policy, render_attempt_schedule


def test_render_retry_policy_default():
    p = RetryPolicy()
    out = render_retry_policy(p)
    assert "Max attempts   : 3" in out
    assert "Initial delay  : 5.0s" in out
    assert "Backoff factor : 1.0x" in out
    assert "any non-zero" in out


def test_render_retry_policy_specific_codes():
    p = RetryPolicy(retry_on_exit_codes=[1, 2])
    out = render_retry_policy(p)
    assert "1, 2" in out
    assert "any non-zero" not in out


def test_render_attempt_schedule_no_backoff():
    p = RetryPolicy(max_attempts=3, delay_seconds=5.0)
    out = render_attempt_schedule(p)
    assert "Attempt 1: immediate" in out
    assert "Attempt 2: after 5.0s" in out
    assert "Attempt 3: after 5.0s" in out


def test_render_attempt_schedule_with_backoff():
    p = RetryPolicy(max_attempts=3, delay_seconds=2.0, backoff_factor=2.0)
    out = render_attempt_schedule(p)
    assert "Attempt 2: after 2.0s" in out
    assert "Attempt 3: after 4.0s" in out


def test_render_single_attempt():
    p = RetryPolicy(max_attempts=1)
    out = render_attempt_schedule(p)
    assert "Attempt 1: immediate" in out
    assert "Attempt 2" not in out

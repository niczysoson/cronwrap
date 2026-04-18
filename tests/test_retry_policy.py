"""Tests for cronwrap.retry_policy."""
import pytest
from cronwrap.retry_policy import RetryPolicy, retry_policy_from_dict, sleep_between_attempts


def _policy(**kw) -> RetryPolicy:
    return RetryPolicy(**kw)


def test_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 3
    assert p.delay_seconds == 5.0
    assert p.backoff_factor == 1.0
    assert p.retry_on_exit_codes is None


def test_invalid_max_attempts():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_invalid_delay():
    with pytest.raises(ValueError):
        RetryPolicy(delay_seconds=-1)


def test_invalid_backoff():
    with pytest.raises(ValueError):
        RetryPolicy(backoff_factor=0.5)


def test_should_retry_any_nonzero():
    p = RetryPolicy(max_attempts=3)
    assert p.should_retry(1, 1) is True
    assert p.should_retry(1, 0) is False
    assert p.should_retry(3, 1) is False  # exhausted


def test_should_retry_specific_codes():
    p = RetryPolicy(max_attempts=3, retry_on_exit_codes=[1, 2])
    assert p.should_retry(1, 1) is True
    assert p.should_retry(1, 2) is True
    assert p.should_retry(1, 3) is False


def test_wait_seconds_no_backoff():
    p = RetryPolicy(delay_seconds=10.0, backoff_factor=1.0)
    assert p.wait_seconds(0) == 0.0
    assert p.wait_seconds(1) == 10.0
    assert p.wait_seconds(2) == 10.0


def test_wait_seconds_with_backoff():
    p = RetryPolicy(delay_seconds=2.0, backoff_factor=2.0)
    assert p.wait_seconds(0) == 0.0
    assert p.wait_seconds(1) == 2.0
    assert p.wait_seconds(2) == 4.0
    assert p.wait_seconds(3) == 8.0


def test_to_dict_round_trip():
    p = RetryPolicy(max_attempts=5, delay_seconds=3.0, backoff_factor=1.5, retry_on_exit_codes=[1])
    p2 = retry_policy_from_dict(p.to_dict())
    assert p2.max_attempts == 5
    assert p2.delay_seconds == 3.0
    assert p2.backoff_factor == 1.5
    assert p2.retry_on_exit_codes == [1]


def test_from_dict_defaults():
    p = retry_policy_from_dict({})
    assert p.max_attempts == 3


def test_sleep_between_attempts_no_wait(monkeypatch):
    calls = []
    monkeypatch.setattr("cronwrap.retry_policy.time.sleep", lambda s: calls.append(s))
    p = RetryPolicy(delay_seconds=5.0)
    sleep_between_attempts(p, 0)  # first attempt — no sleep
    assert calls == []


def test_sleep_between_attempts_waits(monkeypatch):
    calls = []
    monkeypatch.setattr("cronwrap.retry_policy.time.sleep", lambda s: calls.append(s))
    p = RetryPolicy(delay_seconds=4.0, backoff_factor=2.0)
    sleep_between_attempts(p, 1)
    assert calls == [4.0]
    sleep_between_attempts(p, 2)
    assert calls == [4.0, 8.0]

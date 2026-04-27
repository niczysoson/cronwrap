"""Tests for cronwrap.maxage."""
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.maxage import (
    MaxAgeConfig,
    MaxAgeResult,
    maxage_from_dict,
    check_max_age,
)


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# MaxAgeConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = MaxAgeConfig(max_seconds=3600)
    assert cfg.max_seconds == 3600
    assert cfg.enabled is True


def test_config_invalid_max_seconds():
    with pytest.raises(ValueError):
        MaxAgeConfig(max_seconds=0)


def test_config_negative_max_seconds():
    with pytest.raises(ValueError):
        MaxAgeConfig(max_seconds=-10)


def test_maxage_from_dict():
    cfg = maxage_from_dict({"max_seconds": 7200, "enabled": False})
    assert cfg.max_seconds == 7200
    assert cfg.enabled is False


def test_maxage_from_dict_defaults():
    cfg = maxage_from_dict({"max_seconds": 300})
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# check_max_age
# ---------------------------------------------------------------------------

def test_within_limit():
    cfg = MaxAgeConfig(max_seconds=3600)
    last = NOW - timedelta(seconds=1800)
    result = check_max_age(cfg, last_success=last, now=NOW)
    assert not result.exceeded
    assert result.age_seconds == pytest.approx(1800)


def test_exactly_at_limit_not_exceeded():
    cfg = MaxAgeConfig(max_seconds=3600)
    last = NOW - timedelta(seconds=3600)
    result = check_max_age(cfg, last_success=last, now=NOW)
    assert not result.exceeded


def test_exceeds_limit():
    cfg = MaxAgeConfig(max_seconds=3600)
    last = NOW - timedelta(seconds=7200)
    result = check_max_age(cfg, last_success=last, now=NOW)
    assert result.exceeded
    assert result.age_seconds == pytest.approx(7200)


def test_no_previous_success_is_exceeded():
    cfg = MaxAgeConfig(max_seconds=3600)
    result = check_max_age(cfg, last_success=None, now=NOW)
    assert result.exceeded
    assert result.age_seconds is None
    assert result.last_success is None


def test_disabled_never_exceeded():
    cfg = MaxAgeConfig(max_seconds=1, enabled=False)
    last = NOW - timedelta(days=365)
    result = check_max_age(cfg, last_success=last, now=NOW)
    assert not result.exceeded


def test_disabled_no_last_success_not_exceeded():
    cfg = MaxAgeConfig(max_seconds=1, enabled=False)
    result = check_max_age(cfg, last_success=None, now=NOW)
    assert not result.exceeded


# ---------------------------------------------------------------------------
# MaxAgeResult.summary
# ---------------------------------------------------------------------------

def test_summary_within_limit():
    r = MaxAgeResult(last_success=NOW, age_seconds=600, exceeded=False, max_seconds=3600)
    assert "600.0s ago" in r.summary()
    assert "3600.0s" in r.summary()


def test_summary_exceeded():
    r = MaxAgeResult(last_success=NOW, age_seconds=7200, exceeded=True, max_seconds=3600)
    assert "exceeds" in r.summary()


def test_summary_no_previous_success():
    r = MaxAgeResult(last_success=None, age_seconds=None, exceeded=True, max_seconds=3600)
    assert "no previous success" in r.summary()


def test_summary_no_previous_success_not_exceeded():
    r = MaxAgeResult(last_success=None, age_seconds=None, exceeded=False, max_seconds=3600)
    assert "no previous success" in r.summary()

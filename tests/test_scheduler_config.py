"""Tests for CronExpression and JobConfig."""

from datetime import datetime

import pytest

from cronwrap.scheduler import CronExpression
from cronwrap.config import JobConfig


# ---------------------------------------------------------------------------
# CronExpression
# ---------------------------------------------------------------------------

def test_wildcard_matches_any():
    expr = CronExpression("* * * * *")
    assert expr.matches(datetime(2024, 6, 15, 12, 30))


def test_exact_match():
    expr = CronExpression("30 12 15 6 *")
    assert expr.matches(datetime(2024, 6, 15, 12, 30))
    assert not expr.matches(datetime(2024, 6, 15, 12, 31))


def test_step_match():
    expr = CronExpression("*/15 * * * *")
    assert expr.matches(datetime(2024, 1, 1, 0, 0))
    assert expr.matches(datetime(2024, 1, 1, 0, 15))
    assert expr.matches(datetime(2024, 1, 1, 0, 30))
    assert not expr.matches(datetime(2024, 1, 1, 0, 7))


def test_range_match():
    expr = CronExpression("0 9-17 * * *")
    assert expr.matches(datetime(2024, 1, 1, 9, 0))
    assert expr.matches(datetime(2024, 1, 1, 17, 0))
    assert not expr.matches(datetime(2024, 1, 1, 8, 0))


def test_list_match():
    expr = CronExpression("0 8,12,18 * * *")
    assert expr.matches(datetime(2024, 1, 1, 8, 0))
    assert expr.matches(datetime(2024, 1, 1, 12, 0))
    assert not expr.matches(datetime(2024, 1, 1, 10, 0))


def test_invalid_field_count():
    with pytest.raises(ValueError, match="expected 5 fields"):
        CronExpression("* * * *")


def test_out_of_range():
    with pytest.raises(ValueError):
        CronExpression("60 * * * *")


# ---------------------------------------------------------------------------
# JobConfig
# ---------------------------------------------------------------------------

def _base_dict(**overrides):
    data = {"name": "backup", "command": "./backup.sh", "schedule": "0 2 * * *"}
    data.update(overrides)
    return data


def test_from_dict_defaults():
    job = JobConfig.from_dict(_base_dict())
    assert job.retries == 0
    assert job.timeout == 3600
    assert job.alert_on_failure is True
    assert job.tags == []


def test_from_dict_custom_fields():
    job = JobConfig.from_dict(_base_dict(retries=3, timeout=60, tags=["prod"]))
    assert job.retries == 3
    assert job.timeout == 60
    assert job.tags == ["prod"]


def test_from_dict_missing_required():
    with pytest.raises(KeyError, match="Missing required"):
        JobConfig.from_dict({"name": "x", "command": "echo hi"})


def test_invalid_schedule_raises():
    with pytest.raises(ValueError):
        JobConfig.from_dict(_base_dict(schedule="bad expression"))


def test_negative_retries_raises():
    with pytest.raises(ValueError, match="retries"):
        JobConfig(name="x", command="echo", schedule="* * * * *", retries=-1)

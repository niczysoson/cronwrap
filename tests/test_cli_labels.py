import pytest
from cronwrap.cli_labels import parse_selector, render_filtered_jobs, render_grouped_jobs


def _job(name, **labels):
    return {"name": name, "labels": labels}


def test_parse_selector_single():
    assert parse_selector("env=prod") == {"env": "prod"}


def test_parse_selector_multiple():
    assert parse_selector("env=prod,team=ops") == {"env": "prod", "team": "ops"}


def test_parse_selector_invalid():
    with pytest.raises(ValueError):
        parse_selector("envprod")


def test_render_filtered_jobs_match():
    jobs = [_job("backup", env="prod"), _job("sync", env="staging")]
    out = render_filtered_jobs(jobs, "env=prod")
    assert "backup" in out
    assert "sync" not in out


def test_render_filtered_jobs_no_match():
    jobs = [_job("sync", env="staging")]
    out = render_filtered_jobs(jobs, "env=prod")
    assert "No jobs match" in out


def test_render_grouped_jobs():
    jobs = [
        _job("a", env="prod"),
        _job("b", env="staging"),
        _job("c", env="prod"),
    ]
    out = render_grouped_jobs(jobs, "env")
    assert "prod" in out
    assert "staging" in out
    assert "a" in out
    assert "b" in out


def test_render_grouped_jobs_empty():
    out = render_grouped_jobs([], "env")
    assert "No jobs" in out

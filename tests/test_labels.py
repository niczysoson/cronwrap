import pytest
from cronwrap.labels import (
    LabelSet, label_set_from_dict, filter_by_selector, group_jobs_by_label
)


def _job(name, **labels):
    return {"name": name, "labels": labels}


def test_label_set_matches_exact():
    ls = LabelSet(labels={"env": "prod", "team": "ops"})
    assert ls.matches({"env": "prod"})
    assert ls.matches({"env": "prod", "team": "ops"})
    assert not ls.matches({"env": "staging"})


def test_label_set_empty_selector_matches_all():
    ls = LabelSet(labels={"env": "prod"})
    assert ls.matches({})


def test_label_set_get():
    ls = LabelSet(labels={"tier": "web"})
    assert ls.get("tier") == "web"
    assert ls.get("missing", "default") == "default"


def test_label_set_invalid_types():
    with pytest.raises(ValueError):
        LabelSet(labels={1: "val"})


def test_label_set_from_dict():
    ls = label_set_from_dict({"env": "dev"})
    assert ls.get("env") == "dev"


def test_filter_by_selector_returns_matches():
    jobs = [
        _job("a", env="prod"),
        _job("b", env="staging"),
        _job("c", env="prod", team="ops"),
    ]
    result = filter_by_selector(jobs, {"env": "prod"})
    assert len(result) == 2
    assert all(j["labels"]["env"] == "prod" for j in result)


def test_filter_by_selector_no_match():
    jobs = [_job("a", env="dev")]
    assert filter_by_selector(jobs, {"env": "prod"}) == []


def test_filter_by_selector_missing_labels_key():
    jobs = [{"name": "no-labels"}]
    assert filter_by_selector(jobs, {"env": "prod"}) == []


def test_group_jobs_by_label():
    jobs = [
        _job("a", env="prod"),
        _job("b", env="staging"),
        _job("c", env="prod"),
    ]
    groups = group_jobs_by_label(jobs, "env")
    assert len(groups["prod"]) == 2
    assert len(groups["staging"]) == 1


def test_group_jobs_unset_label():
    jobs = [_job("a"), _job("b", env="prod")]
    groups = group_jobs_by_label(jobs, "env")
    assert "__unset__" in groups
    assert len(groups["__unset__"]) == 1

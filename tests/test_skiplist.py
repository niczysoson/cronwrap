import pytest
from cronwrap.skiplist import SkipConfig, skiplist_from_dict


def test_default_config_skips_nothing():
    cfg = SkipConfig()
    assert cfg.should_skip(1) is False
    assert cfg.should_skip(0) is False


def test_skip_by_exit_code():
    cfg = SkipConfig(exit_codes=[2, 75])
    assert cfg.should_skip(2) is True
    assert cfg.should_skip(75) is True
    assert cfg.should_skip(1) is False


def test_skip_by_stdout_pattern():
    cfg = SkipConfig(stdout_patterns=["nothing to do"])
    assert cfg.should_skip(1, stdout="nothing to do here") is True
    assert cfg.should_skip(1, stdout="failed badly") is False


def test_skip_by_stderr_pattern():
    cfg = SkipConfig(stderr_patterns=["already up-to-date"])
    assert cfg.should_skip(1, stderr="already up-to-date") is True
    assert cfg.should_skip(1, stderr="error occurred") is False


def test_disabled_never_skips():
    cfg = SkipConfig(exit_codes=[1, 2], stdout_patterns=["ok"], enabled=False)
    assert cfg.should_skip(1, stdout="ok") is False


def test_invalid_exit_codes_type():
    with pytest.raises(ValueError):
        SkipConfig(exit_codes="1,2")


def test_invalid_exit_code_element():
    with pytest.raises(ValueError):
        SkipConfig(exit_codes=["one"])


def test_invalid_stdout_patterns_type():
    with pytest.raises(ValueError):
        SkipConfig(stdout_patterns="pattern")


def test_to_dict_round_trip():
    cfg = SkipConfig(exit_codes=[3], stdout_patterns=["skip me"], stderr_patterns=["ignore"])
    d = cfg.to_dict()
    assert d["exit_codes"] == [3]
    assert d["stdout_patterns"] == ["skip me"]
    assert d["stderr_patterns"] == ["ignore"]
    assert d["enabled"] is True


def test_skiplist_from_dict():
    cfg = skiplist_from_dict({"exit_codes": [99], "enabled": False})
    assert cfg.exit_codes == [99]
    assert cfg.enabled is False
    assert cfg.stdout_patterns == []


def test_skiplist_from_dict_defaults():
    cfg = skiplist_from_dict({})
    assert cfg.exit_codes == []
    assert cfg.enabled is True

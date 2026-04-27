"""Tests for cronwrap.fencing and cronwrap.cli_fencing."""
from __future__ import annotations

import pytest

from cronwrap.fencing import (
    FenceConfig,
    FenceResult,
    check_fence,
    fence_from_dict,
)
from cronwrap.cli_fencing import (
    render_fence_config,
    render_fence_result,
    check_and_exit_if_fenced,
)


# ---------------------------------------------------------------------------
# FenceConfig validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = FenceConfig(allowed_hosts=["host-a", "host-b"])
    assert cfg.allowed_hosts == ["host-a", "host-b"]
    assert cfg.enabled is True


def test_config_invalid_hosts_type():
    with pytest.raises(ValueError, match="must be a list"):
        FenceConfig(allowed_hosts="host-a")  # type: ignore[arg-type]


def test_config_invalid_empty_string_in_hosts():
    with pytest.raises(ValueError, match="non-empty string"):
        FenceConfig(allowed_hosts=["host-a", ""])


# ---------------------------------------------------------------------------
# fence_from_dict
# ---------------------------------------------------------------------------

def test_fence_from_dict():
    cfg = fence_from_dict({"allowed_hosts": ["web-01"], "enabled": False})
    assert cfg.allowed_hosts == ["web-01"]
    assert cfg.enabled is False


def test_fence_from_dict_defaults():
    cfg = fence_from_dict({})
    assert cfg.allowed_hosts == []
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# check_fence
# ---------------------------------------------------------------------------

def test_allowed_host_passes():
    cfg = FenceConfig(allowed_hosts=["builder-1", "builder-2"])
    result = check_fence(cfg, hostname="builder-1")
    assert result.allowed is True
    assert result.current_host == "builder-1"


def test_disallowed_host_blocked():
    cfg = FenceConfig(allowed_hosts=["builder-1"])
    result = check_fence(cfg, hostname="rogue-host")
    assert result.allowed is False
    assert "rogue-host" in result.summary()


def test_disabled_fencing_always_allows():
    cfg = FenceConfig(allowed_hosts=["builder-1"], enabled=False)
    result = check_fence(cfg, hostname="any-host")
    assert result.allowed is True


def test_empty_allowed_list_allows_all():
    cfg = FenceConfig(allowed_hosts=[])
    result = check_fence(cfg, hostname="unknown-host")
    assert result.allowed is True


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_render_fence_config_disabled():
    cfg = FenceConfig(enabled=False)
    assert "disabled" in render_fence_config(cfg)


def test_render_fence_config_no_restrictions():
    cfg = FenceConfig(allowed_hosts=[])
    assert "no host restrictions" in render_fence_config(cfg)


def test_render_fence_config_with_hosts():
    cfg = FenceConfig(allowed_hosts=["prod-1", "prod-2"])
    out = render_fence_config(cfg)
    assert "prod-1" in out and "prod-2" in out


def test_render_fence_result_allowed():
    r = FenceResult(allowed=True, current_host="h1", allowed_hosts=["h1"])
    assert "✓" in render_fence_result(r)


def test_render_fence_result_blocked():
    r = FenceResult(allowed=False, current_host="h2", allowed_hosts=["h1"])
    assert "✗" in render_fence_result(r)


def test_check_and_exit_passes(capsys):
    cfg = FenceConfig(allowed_hosts=["allowed-host"])
    result = check_and_exit_if_fenced(cfg, hostname="allowed-host", verbose=True)
    assert result.allowed is True
    captured = capsys.readouterr()
    assert "✓" in captured.out


def test_check_and_exit_blocked(capsys):
    cfg = FenceConfig(allowed_hosts=["allowed-host"])
    with pytest.raises(SystemExit) as exc_info:
        check_and_exit_if_fenced(cfg, hostname="bad-host")
    assert exc_info.value.code == 1

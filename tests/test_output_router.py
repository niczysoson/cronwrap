"""Tests for cronwrap.output_router."""
import os
import pytest
from cronwrap.runner import RunResult
from cronwrap.output_router import (
    OutputRoute,
    route_from_dict,
    apply_output_route,
    render_route,
)


def _result(stdout="hello\n", stderr="warn\n", rc=0):
    return RunResult(returncode=rc, stdout=stdout, stderr=stderr, duration=0.1)


def test_default_route_passthrough():
    route = OutputRoute()
    out = apply_output_route(_result(), route)
    assert out.stdout == "hello\n"
    assert out.stderr == "warn\n"


def test_suppress_stdout():
    route = OutputRoute(suppress_stdout=True)
    out = apply_output_route(_result(), route)
    assert out.stdout == ""
    assert out.stderr == "warn\n"


def test_suppress_stderr():
    route = OutputRoute(suppress_stderr=True)
    out = apply_output_route(_result(), route)
    assert out.stdout == "hello\n"
    assert out.stderr == ""


def test_write_stdout_to_file(tmp_path):
    dest = str(tmp_path / "out.log")
    route = OutputRoute(stdout_file=dest)
    apply_output_route(_result(stdout="job output\n"), route)
    assert open(dest).read() == "job output\n"


def test_write_stderr_to_file(tmp_path):
    dest = str(tmp_path / "err.log")
    route = OutputRoute(stderr_file=dest)
    apply_output_route(_result(stderr="error line\n"), route)
    assert open(dest).read() == "error line\n"


def test_append_mode(tmp_path):
    dest = str(tmp_path / "out.log")
    route = OutputRoute(stdout_file=dest, append=True)
    apply_output_route(_result(stdout="first\n"), route)
    apply_output_route(_result(stdout="second\n"), route)
    assert open(dest).read() == "first\nsecond\n"


def test_conflict_stdout_raises():
    with pytest.raises(ValueError):
        OutputRoute(stdout_file="/tmp/x.log", suppress_stdout=True)


def test_conflict_stderr_raises():
    with pytest.raises(ValueError):
        OutputRoute(stderr_file="/tmp/x.log", suppress_stderr=True)


def test_route_from_dict():
    route = route_from_dict({"suppress_stdout": True, "append": True})
    assert route.suppress_stdout is True
    assert route.append is True
    assert route.stdout_file is None


def test_render_route_passthrough():
    text = render_route(OutputRoute())
    assert "passthrough" in text


def test_render_route_suppressed():
    text = render_route(OutputRoute(suppress_stdout=True, suppress_stderr=True))
    assert text.count("suppressed") == 2

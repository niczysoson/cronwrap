"""Tests for the cronwrap CLI."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from cronwrap.cli import main
from cronwrap.runner import RunResult


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "history.json")


def _mock_success_result():
    return RunResult(success=True, returncode=0, stdout="ok", stderr="", attempts=1, duration=0.1)


def _mock_failure_result():
    return RunResult(success=False, returncode=1, stdout="", stderr="err", attempts=1, duration=0.1)


def test_exec_success(history_file):
    with patch("cronwrap.cli.run", return_value=_mock_success_result()) as mock_run:
        rc = main(["exec", "--name", "myjob", "--cmd", "echo hi", "--history", history_file])
    assert rc == 0
    mock_run.assert_called_once()


def test_exec_failure(history_file):
    with patch("cronwrap.cli.run", return_value=_mock_failure_result()):
        rc = main(["exec", "--name", "myjob", "--cmd", "false", "--history", history_file])
    assert rc == 1


def test_exec_passes_retries(history_file):
    with patch("cronwrap.cli.run", return_value=_mock_success_result()) as mock_run:
        main(["exec", "--name", "j", "--cmd", "true", "--retries", "3", "--history", history_file])
    config = mock_run.call_args[0][0]
    assert config.retries == 3


def test_status_no_history(history_file, capsys):
    rc = main(["status", "--history", history_file])
    assert rc == 0
    captured = capsys.readouterr()
    assert isinstance(captured.out, str)


def test_status_with_name(history_file, capsys):
    rc = main(["status", "--name", "somejob", "--history", history_file])
    assert rc == 0
    captured = capsys.readouterr()
    assert "somejob" in captured.out


def test_no_command_prints_help(capsys):
    rc = main([])
    assert rc == 1

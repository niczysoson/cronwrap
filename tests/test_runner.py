import sys
import pytest
from unittest.mock import patch, MagicMock
from cronwrap.runner import run


def _make_result(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def test_successful_command():
    with patch("cronwrap.runner.subprocess.run") as mock_run:
        mock_run.return_value = _make_result(0, stdout="hello")
        code = run(["echo", "hello"], job_name="test_success")
    assert code == 0
    mock_run.assert_called_once()


def test_failed_command_no_retries():
    with patch("cronwrap.runner.subprocess.run") as mock_run:
        mock_run.return_value = _make_result(1, stderr="error")
        code = run(["false"], job_name="test_fail")
    assert code == 1
    assert mock_run.call_count == 1


def test_retry_logic_success_on_second_attempt():
    with patch("cronwrap.runner.subprocess.run") as mock_run, \
         patch("cronwrap.runner.time.sleep") as mock_sleep:
        mock_run.side_effect = [
            _make_result(1),
            _make_result(0),
        ]
        code = run(["flaky"], retries=1, retry_delay=0.0, job_name="test_retry")
    assert code == 0
    assert mock_run.call_count == 2
    mock_sleep.assert_called_once_with(0.0)


def test_all_retries_exhausted():
    with patch("cronwrap.runner.subprocess.run") as mock_run, \
         patch("cronwrap.runner.time.sleep"):
        mock_run.return_value = _make_result(1)
        code = run(["bad"], retries=2, retry_delay=0.0, job_name="test_exhausted")
    assert code == 1
    assert mock_run.call_count == 3


def test_timeout_triggers_retry():
    import subprocess
    with patch("cronwrap.runner.subprocess.run") as mock_run, \
         patch("cronwrap.runner.time.sleep"):
        mock_run.side_effect = [
            subprocess.TimeoutExpired(cmd="slow", timeout=1),
            _make_result(0),
        ]
        code = run(["slow"], retries=1, timeout=1, retry_delay=0.0, job_name="test_timeout")
    assert code == 0
    assert mock_run.call_count == 2

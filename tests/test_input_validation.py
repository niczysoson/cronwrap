"""Tests for cronwrap.input_validation."""
import pytest
from cronwrap.input_validation import (
    validate_command,
    validate_job_name,
    validation_from_dict,
    ValidationResult,
)


def test_valid_simple_command():
    r = validate_command("echo hello")
    assert r.ok
    assert not r.errors


def test_empty_command_invalid():
    r = validate_command("")
    assert not r.ok
    assert any("empty" in e.lower() for e in r.errors)


def test_whitespace_only_command_invalid():
    r = validate_command("   ")
    assert not r.ok


def test_dangerous_pattern_warns():
    r = validate_command("ls; rm -rf /tmp/test")
    assert r.warnings


def test_shell_operator_blocked_by_default():
    r = validate_command("echo a && echo b")
    assert not r.ok
    assert any("Shell operators" in e for e in r.errors)


def test_shell_operator_allowed_with_flag():
    r = validate_command("echo a && echo b", allow_shell=True)
    assert r.ok


def test_malformed_quotes_invalid():
    r = validate_command("echo 'unclosed")
    assert not r.ok
    assert any("parse error" in e.lower() for e in r.errors)


def test_valid_job_name():
    r = validate_job_name("my-job_01")
    assert r.ok


def test_empty_job_name_invalid():
    r = validate_job_name("")
    assert not r.ok


def test_job_name_with_spaces_invalid():
    r = validate_job_name("my job")
    assert not r.ok
    assert any("Invalid job name" in e for e in r.errors)


def test_job_name_special_chars_invalid():
    r = validate_job_name("job@prod")
    assert not r.ok


def test_validation_from_dict_all_valid():
    r = validation_from_dict({"name": "backup-db", "command": "pg_dump mydb"})
    assert r.ok


def test_validation_from_dict_bad_name_and_command():
    r = validation_from_dict({"name": "bad name!", "command": ""})
    assert not r.ok
    assert len(r.errors) >= 2


def test_summary_ok():
    r = ValidationResult(valid=True)
    assert r.summary() == "  OK"


def test_summary_with_errors_and_warnings():
    r = ValidationResult(valid=False, errors=["bad"], warnings=["careful"])
    s = r.summary()
    assert "ERROR" in s
    assert "WARNING" in s

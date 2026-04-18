"""Tests for cronwrap.audit and cronwrap.cli_audit."""
import pytest
from pathlib import Path

from cronwrap.audit import AuditEvent, AuditLog
from cronwrap.cli_audit import render_audit_events


@pytest.fixture
def audit_file(tmp_path) -> AuditLog:
    return AuditLog(str(tmp_path / "audit.log"))


def _ev(job="backup", event="succeeded", detail=None, exit_code=None):
    return AuditEvent(job_name=job, event=event, detail=detail, exit_code=exit_code)


def test_record_and_read(audit_file):
    audit_file.record(_ev())
    events = audit_file.read_all()
    assert len(events) == 1
    assert events[0].job_name == "backup"
    assert events[0].event == "succeeded"


def test_multiple_events_persisted(audit_file):
    for ev in ["started", "retry", "succeeded"]:
        audit_file.record(_ev(event=ev))
    assert len(audit_file.read_all()) == 3


def test_filter_by_job(audit_file):
    audit_file.record(_ev(job="backup"))
    audit_file.record(_ev(job="report"))
    results = audit_file.filter(job_name="backup")
    assert all(e.job_name == "backup" for e in results)
    assert len(results) == 1


def test_filter_by_event(audit_file):
    audit_file.record(_ev(event="failed", exit_code=1))
    audit_file.record(_ev(event="succeeded"))
    results = audit_file.filter(event="failed")
    assert len(results) == 1
    assert results[0].exit_code == 1


def test_empty_log_returns_empty(audit_file):
    assert audit_file.read_all() == []


def test_roundtrip_to_dict():
    ev = _ev(detail="ok", exit_code=0)
    restored = AuditEvent.from_dict(ev.to_dict())
    assert restored.job_name == ev.job_name
    assert restored.detail == "ok"
    assert restored.exit_code == 0


def test_render_no_events():
    assert render_audit_events([]) == "No audit events found."


def test_render_shows_symbol():
    output = render_audit_events([_ev(event="failed", exit_code=2)])
    assert "✘" in output
    assert "exit=2" in output


def test_render_limit():
    events = [_ev(event="succeeded") for _ in range(10)]
    output = render_audit_events(events, limit=3)
    assert output.count("succeeded") == 3

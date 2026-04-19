"""Tests for cronwrap.tracing and cronwrap.cli_tracing."""
import time
from pathlib import Path

import pytest

from cronwrap.tracing import Span, TraceStore
from cronwrap.cli_tracing import render_spans, render_trace, render_job_traces


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "traces.jsonl"


def _make_span(name="step", job="backup", status="ok") -> Span:
    s = Span(name=name, job_name=job)
    s.finish(status)
    return s


def test_span_duration():
    s = Span(name="run", job_name="myjob")
    time.sleep(0.01)
    s.finish("ok")
    assert s.duration_seconds is not None
    assert s.duration_seconds >= 0.01


def test_span_round_trip():
    s = _make_span()
    d = s.to_dict()
    s2 = Span.from_dict(d)
    assert s2.trace_id == s.trace_id
    assert s2.span_id == s.span_id
    assert s2.status == "ok"
    assert s2.duration_seconds == s.duration_seconds


def test_span_running_has_no_duration():
    s = Span(name="run", job_name="job")
    assert s.duration_seconds is None


def test_store_record_and_all(store_path):
    store = TraceStore(store_path)
    s = _make_span()
    store.record(s)
    all_spans = store.all()
    assert len(all_spans) == 1
    assert all_spans[0].span_id == s.span_id


def test_store_empty(store_path):
    store = TraceStore(store_path)
    assert store.all() == []


def test_store_for_job(store_path):
    store = TraceStore(store_path)
    store.record(_make_span(job="backup"))
    store.record(_make_span(job="cleanup"))
    assert len(store.for_job("backup")) == 1
    assert len(store.for_job("cleanup")) == 1
    assert store.for_job("missing") == []


def test_store_for_trace(store_path):
    store = TraceStore(store_path)
    s1 = _make_span()
    s2 = _make_span()
    store.record(s1)
    store.record(s2)
    result = store.for_trace(s1.trace_id)
    assert len(result) == 1
    assert result[0].span_id == s1.span_id


def test_render_spans_empty():
    assert "No spans" in render_spans([])


def test_render_spans_ok():
    s = _make_span(name="fetch", status="ok")
    out = render_spans([s])
    assert "fetch" in out
    assert "✓" in out


def test_render_spans_error():
    s = _make_span(name="upload", status="error")
    out = render_spans([s])
    assert "✗" in out


def test_render_trace():
    s = _make_span()
    out = render_trace(s.trace_id, [s])
    assert s.trace_id in out
    assert "1 span" in out


def test_render_job_traces_empty():
    out = render_job_traces("myjob", [])
    assert "myjob" in out
    assert "No traces" in out


def test_render_job_traces_groups_by_trace():
    s1 = _make_span(name="a", job="j")
    s2 = _make_span(name="b", job="j")
    # force same trace
    s2.trace_id = s1.trace_id
    out = render_job_traces("j", [s1, s2])
    assert out.count(s1.trace_id) >= 1

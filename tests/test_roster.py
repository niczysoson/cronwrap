"""Tests for cronwrap.roster and cronwrap.cli_roster."""
import pytest
from pathlib import Path

from cronwrap.roster import Roster, RosterEntry, roster_from_dict
from cronwrap.cli_roster import (
    render_roster_table,
    render_roster_entry,
    render_filtered_by_tag,
)


@pytest.fixture
def roster_file(tmp_path) -> Path:
    return tmp_path / "roster.json"


def _entry(name="backup", schedule="0 2 * * *", tags=None, enabled=True):
    return RosterEntry(
        name=name,
        command=f"run_{name}.sh",
        schedule=schedule,
        tags=tags or ["daily"],
        enabled=enabled,
        description=f"Job {name}",
    )


def test_register_and_get(roster_file):
    r = Roster(roster_file)
    e = _entry()
    r.register(e)
    assert r.get("backup") is not None
    assert r.get("backup").command == "run_backup.sh"


def test_persists_to_disk(roster_file):
    r = Roster(roster_file)
    r.register(_entry("sync"))
    r2 = Roster(roster_file)
    assert r2.get("sync") is not None


def test_unregister_removes_entry(roster_file):
    r = Roster(roster_file)
    r.register(_entry())
    removed = r.unregister("backup")
    assert removed is True
    assert r.get("backup") is None


def test_unregister_missing_returns_false(roster_file):
    r = Roster(roster_file)
    assert r.unregister("nonexistent") is False


def test_enabled_filters_disabled(roster_file):
    r = Roster(roster_file)
    r.register(_entry("a", enabled=True))
    r.register(_entry("b", enabled=False))
    names = [e.name for e in r.enabled()]
    assert "a" in names
    assert "b" not in names


def test_by_tag(roster_file):
    r = Roster(roster_file)
    r.register(_entry("nightly", tags=["nightly", "db"]))
    r.register(_entry("daily", tags=["daily"]))
    db_jobs = r.by_tag("db")
    assert len(db_jobs) == 1
    assert db_jobs[0].name == "nightly"


def test_roster_from_dict(roster_file):
    r = roster_from_dict({"roster_file": str(roster_file)})
    assert isinstance(r, Roster)


def test_round_trip_dict():
    e = _entry("export", tags=["weekly"])
    e2 = RosterEntry.from_dict(e.to_dict())
    assert e2.name == e.name
    assert e2.tags == e.tags
    assert e2.enabled == e.enabled


def test_render_table_empty(roster_file):
    r = Roster(roster_file)
    out = render_roster_table(r)
    assert "No jobs" in out


def test_render_table_with_entries(roster_file):
    r = Roster(roster_file)
    r.register(_entry())
    out = render_roster_table(r)
    assert "backup" in out
    assert "0 2 * * *" in out


def test_render_entry():
    e = _entry()
    out = render_roster_entry(e)
    assert "backup" in out
    assert "run_backup.sh" in out


def test_render_filtered_by_tag_match(roster_file):
    r = Roster(roster_file)
    r.register(_entry("db-backup", tags=["db", "daily"]))
    out = render_filtered_by_tag(r, "db")
    assert "db-backup" in out


def test_render_filtered_by_tag_no_match(roster_file):
    r = Roster(roster_file)
    out = render_filtered_by_tag(r, "missing")
    assert "No jobs" in out

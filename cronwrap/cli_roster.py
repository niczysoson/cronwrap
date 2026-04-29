"""CLI rendering helpers for the job roster."""
from __future__ import annotations

from typing import List

from cronwrap.roster import Roster, RosterEntry


def _enabled_symbol(entry: RosterEntry) -> str:
    return "✓" if entry.enabled else "✗"


def render_roster_table(roster: Roster) -> str:
    entries = roster.all()
    if not entries:
        return "No jobs registered."

    lines = [
        f"{'ST':<3} {'NAME':<24} {'SCHEDULE':<20} {'TAGS':<20} DESCRIPTION",
        "-" * 80,
    ]
    for e in entries:
        tags = ",".join(e.tags) if e.tags else "-"
        desc = e.description[:28] if e.description else "-"
        lines.append(f"{_enabled_symbol(e):<3} {e.name:<24} {e.schedule:<20} {tags:<20} {desc}")
    return "\n".join(lines)


def render_roster_entry(entry: RosterEntry) -> str:
    lines = [
        f"Job      : {entry.name}",
        f"Command  : {entry.command}",
        f"Schedule : {entry.schedule}",
        f"Enabled  : {entry.enabled}",
        f"Tags     : {', '.join(entry.tags) if entry.tags else 'none'}",
        f"Desc     : {entry.description or 'none'}",
    ]
    return "\n".join(lines)


def render_filtered_by_tag(roster: Roster, tag: str) -> str:
    entries = roster.by_tag(tag)
    if not entries:
        return f"No jobs with tag '{tag}'."
    lines = [f"Jobs tagged '{tag}':", "-" * 40]
    for e in entries:
        status = "enabled" if e.enabled else "disabled"
        lines.append(f"  {_enabled_symbol(e)} {e.name:<24} [{status}]")
    return "\n".join(lines)

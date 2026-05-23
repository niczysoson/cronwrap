"""CLI sub-commands for managing manual triggers.

Usage examples::

    python -m cronwrap trigger set   --job backup
    python -m cronwrap trigger clear --job backup
    python -m cronwrap trigger status --job backup
"""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.trigger import TriggerConfig, trigger_from_dict
from cronwrap.cli_trigger import render_trigger_status


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap trigger",
        description="Manage manual job triggers.",
    )
    p.add_argument("action", choices=["set", "clear", "status"],
                   help="Action to perform.")
    p.add_argument("--job", required=True, help="Job name.")
    p.add_argument(
        "--config",
        default="{}",
        help="JSON-encoded TriggerConfig overrides.",
    )
    return p


def cmd_trigger(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        raw = json.loads(args.config)
    except json.JSONDecodeError as exc:
        print(f"[cronwrap] invalid --config JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    try:
        cfg = trigger_from_dict(raw)
    except ValueError as exc:
        print(f"[cronwrap] invalid trigger config: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if args.action == "set":
        cfg.set_trigger(args.job)
        print(f"[cronwrap] trigger set for '{args.job}'.")
    elif args.action == "clear":
        cfg.clear_trigger(args.job)
        print(f"[cronwrap] trigger cleared for '{args.job}'.")
    else:  # status
        print(render_trigger_status(cfg, args.job))


if __name__ == "__main__":  # pragma: no cover
    cmd_trigger()

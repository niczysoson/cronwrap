"""CLI sub-command: cronwrap isolation — inspect or test isolation config."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .isolation import IsolationConfig, isolation_from_dict
from .cli_isolation import render_isolation_config, summarise_env


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap isolation",
        description="Inspect job environment isolation configuration.",
    )
    sub = p.add_subparsers(dest="subcmd")

    show = sub.add_parser("show", help="Show isolation config from JSON")
    show.add_argument(
        "--config",
        default="{}",
        help="JSON string with isolation config (default: empty)",
    )

    preview = sub.add_parser("preview", help="Preview the environment that would be passed")
    preview.add_argument(
        "--config",
        default="{}",
        help="JSON string with isolation config",
    )
    return p


def cmd_isolation(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.subcmd == "show":
        try:
            data = json.loads(args.config)
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON — {exc}", file=sys.stderr)
            return 2
        try:
            cfg = isolation_from_dict(data)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        for line in render_isolation_config(cfg):
            print(line)
        return 0

    if args.subcmd == "preview":
        try:
            data = json.loads(args.config)
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON — {exc}", file=sys.stderr)
            return 2
        try:
            cfg = isolation_from_dict(data)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        env = cfg.build_env()
        print(summarise_env(env))
        for k in sorted(env):
            print(f"  {k}={env[k]}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cmd_isolation())

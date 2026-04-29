"""CLI sub-command: cronwrap notify-window."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .notifywindow import notify_window_from_dict, is_notify_allowed
from .cli_notifywindow import (
    render_notify_window_config,
    render_notify_window_result,
    check_and_exit_if_suppressed,
)


def _build_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="cronwrap notify-window",
        description="Check or display the notification window configuration.",
    )
    sub = p.add_subparsers(dest="nw_cmd")

    show = sub.add_parser("show", help="Display the notify-window config.")
    show.add_argument(
        "--config",
        default="{}",
        help="JSON config for NotifyWindowConfig.",
    )

    check = sub.add_parser(
        "check",
        help="Exit non-zero if notifications are currently suppressed.",
    )
    check.add_argument("--config", default="{}", help="JSON config.")
    check.add_argument(
        "--exit-code",
        type=int,
        default=0,
        help="Exit code to use when suppressed (default: 0).",
    )
    check.add_argument(
        "--time",
        default=None,
        help="Override current time as HH:MM (for testing).",
    )

    return p


def cmd_notify_window(args: argparse.Namespace) -> None:
    try:
        raw = json.loads(args.config)
        cfg = notify_window_from_dict(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.nw_cmd == "show":
        print(render_notify_window_config(cfg))
        result = is_notify_allowed(cfg)
        print(render_notify_window_result(result))

    elif args.nw_cmd == "check":
        now: datetime | None = None
        if args.time:
            try:
                h, m = map(int, args.time.split(":"))
                now = datetime.utcnow().replace(hour=h, minute=m, second=0, microsecond=0)
            except ValueError:
                print(f"Invalid --time value: {args.time}", file=sys.stderr)
                sys.exit(1)
        check_and_exit_if_suppressed(cfg, now=now, exit_code=args.exit_code)

    else:
        _build_parser().print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    _parser = _build_parser()
    cmd_notify_window(_parser.parse_args())

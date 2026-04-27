"""CLI sub-command: cronwrap fence-check."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.fencing import fence_from_dict, check_fence
from cronwrap.cli_fencing import render_fence_config, render_fence_result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap fence-check",
        description="Verify the current host is allowed to run a job.",
    )
    p.add_argument(
        "--hosts",
        nargs="+",
        metavar="HOST",
        default=[],
        help="Allowed hostnames. If omitted, all hosts are permitted.",
    )
    p.add_argument(
        "--hostname",
        default=None,
        help="Override the detected hostname (useful for testing).",
    )
    p.add_argument(
        "--disabled",
        action="store_true",
        help="Treat fencing as disabled (always allow).",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output result as JSON.",
    )
    return p


def cmd_fence_check(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = fence_from_dict(
        {"allowed_hosts": args.hosts, "enabled": not args.disabled}
    )

    result = check_fence(config, hostname=args.hostname)

    if args.output_json:
        data = {
            "allowed": result.allowed,
            "current_host": result.current_host,
            "allowed_hosts": result.allowed_hosts,
            "summary": result.summary(),
        }
        print(json.dumps(data, indent=2))
    else:
        print(render_fence_config(config))
        print(render_fence_result(result))

    if not result.allowed:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    cmd_fence_check()

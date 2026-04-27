"""CLI command for inspecting job maturity from the command line."""
from __future__ import annotations

import argparse
import sys

from cronwrap.maturity import MaturityConfig, check_maturity
from cronwrap.cli_maturity import render_maturity_result
from cronwrap.history import JobHistory


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap maturity",
        description="Check whether a job last succeeded within the allowed age window.",
    )
    p.add_argument("job_name", help="Name of the cron job to inspect")
    p.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        metavar="HOURS",
        help="Maximum acceptable age of the last successful run (default: 24)",
    )
    p.add_argument(
        "--history-file",
        default=".cronwrap_history.json",
        metavar="PATH",
        help="Path to the job history file",
    )
    p.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 even when the job is stale (useful for monitoring)",
    )
    return p


def cmd_maturity(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = MaturityConfig(
            max_age_hours=args.max_age_hours,
            job_name=args.job_name,
        )
    except ValueError as exc:
        parser.error(str(exc))

    history = JobHistory(path=args.history_file)
    result = check_maturity(cfg, history)

    print(render_maturity_result(result))

    if result.is_mature and not args.exit_zero:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    cmd_maturity()

"""Command-line interface for cronwrap."""
import argparse
import sys
from datetime import datetime

from cronwrap.config import JobConfig
from cronwrap.history import JobHistory
from cronwrap.dashboard import render_all_jobs, render_job_summary
from cronwrap.runner import run
from cronwrap.alerting import from_env


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Lightweight cron job wrapper with logging, alerting, and retry logic.",
    )
    sub = parser.add_subparsers(dest="command")

    exec_p = sub.add_parser("exec", help="Execute a cron job command.")
    exec_p.add_argument("--name", required=True, help="Job name")
    exec_p.add_argument("--cmd", required=True, help="Shell command to run")
    exec_p.add_argument("--retries", type=int, default=0, help="Number of retries")
    exec_p.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    exec_p.add_argument("--history", default=".cronwrap_history.json", help="History file path")

    status_p = sub.add_parser("status", help="Show job run history.")
    status_p.add_argument("--name", default=None, help="Filter by job name")
    status_p.add_argument("--limit", type=int, default=10, help="Number of entries to show")
    status_p.add_argument("--history", default=".cronwrap_history.json", help="History file path")

    return parser


def cmd_exec(args) -> int:
    alert_config = from_env()
    history = JobHistory(args.history)
    config = JobConfig(
        name=args.name,
        command=args.cmd,
        schedule="* * * * *",
        retries=args.retries,
        timeout=args.timeout,
    )
    result = run(config, alert_config=alert_config, history=history)
    return 0 if result.success else 1


def cmd_status(args) -> int:
    history = JobHistory(args.history)
    if args.name:
        print(render_job_summary(args.name, history, limit=args.limit))
    else:
        print(render_all_jobs(history, limit=args.limit))
    return 0


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "exec":
        return cmd_exec(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

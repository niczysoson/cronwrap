"""Command-line interface for cronwrap."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.runner import run
from cronwrap.history import JobHistory
from cronwrap.dashboard import render_all_jobs, render_job_summary
from cronwrap.concurrency import ConcurrencyConfig, acquire_slot, release_slot
from cronwrap.cli_concurrency import render_concurrency_status


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap", description="Cron job wrapper")
    sub = p.add_subparsers(dest="command")

    ex = sub.add_parser("exec", help="Execute a command")
    ex.add_argument("cmd", nargs=argparse.REMAINDER)
    ex.add_argument("--job", default="default", help="Job name")
    ex.add_argument("--retries", type=int, default=0)
    ex.add_argument("--history-file", default="/tmp/cronwrap_history.json")
    ex.add_argument("--max-concurrent", type=int, default=0,
                    help="Max concurrent instances (0 = unlimited)")
    ex.add_argument("--lock-dir", default="/tmp/cronwrap_concurrency")

    st = sub.add_parser("status", help="Show job history")
    st.add_argument("--job", default=None)
    st.add_argument("--history-file", default="/tmp/cronwrap_history.json")
    st.add_argument("--limit", type=int, default=10)

    cc = sub.add_parser("concurrency", help="Show concurrency status")
    cc.add_argument("--job", required=True)
    cc.add_argument("--max-concurrent", type=int, default=1)
    cc.add_argument("--lock-dir", default="/tmp/cronwrap_concurrency")

    return p


def cmd_exec(args: argparse.Namespace) -> None:
    slot = None
    if args.max_concurrent > 0:
        from cronwrap.cli_concurrency import check_and_exit_if_at_limit
        cfg = ConcurrencyConfig(max_concurrent=args.max_concurrent, lock_dir=args.lock_dir)
        slot = check_and_exit_if_at_limit(args.job, cfg)

    try:
        history = JobHistory(args.history_file)
        result = run(args.cmd, retries=args.retries)
        history.record(args.job, result)
        if not result.succeeded:
            sys.exit(result.returncode or 1)
    finally:
        if slot:
            release_slot(slot)


def cmd_status(args: argparse.Namespace) -> None:
    history = JobHistory(args.history_file)
    if args.job:
        print(render_job_summary(args.job, history, limit=args.limit))
    else:
        print(render_all_jobs(history, limit=args.limit))


def cmd_concurrency(args: argparse.Namespace) -> None:
    cfg = ConcurrencyConfig(max_concurrent=args.max_concurrent, lock_dir=args.lock_dir)
    print(render_concurrency_status(args.job, cfg))


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "exec":
        cmd_exec(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "concurrency":
        cmd_concurrency(args)
    else:
        parser.print_help()

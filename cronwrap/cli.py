"""CLI entry point for cronwrap."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap import runner
from cronwrap.history import History
from cronwrap.dashboard import render_all_jobs
from cronwrap.concurrency import ConcurrencyConfig, concurrency_from_dict
from cronwrap.cli_concurrency import render_concurrency_status, check_and_exit_if_at_limit
from cronwrap.progress import load_progress
from cronwrap.cli_progress import print_progress


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap", description="Cron job wrapper")
    sub = p.add_subparsers(dest="command")

    ex = sub.add_parser("exec", help="Run a cron job command")
    ex.add_argument("--job", required=True)
    ex.add_argument("--cmd", required=True)
    ex.add_argument("--retries", type=int, default=0)
    ex.add_argument("--history-file", default=".cronwrap_history.json")

    st = sub.add_parser("status", help="Show job history dashboard")
    st.add_argument("--history-file", default=".cronwrap_history.json")
    st.add_argument("--limit", type=int, default=5)

    cc = sub.add_parser("concurrency", help="Check concurrency slot status")
    cc.add_argument("--job", required=True)
    cc.add_argument("--max-slots", type=int, default=1)
    cc.add_argument("--lock-dir", default="/tmp/cronwrap_locks")

    pg = sub.add_parser("progress", help="Show step progress for a job")
    pg.add_argument("--file", required=True, help="Path to progress JSON file")

    return p


def cmd_exec(args: argparse.Namespace) -> int:
    history = History(path=Path(args.history_file))
    result = runner.run(args.cmd, retries=args.retries)
    history.record(job_name=args.job, result=result)
    if result.returncode == 0:
        print(f"[OK] {args.job}")
        return 0
    print(f"[FAIL] {args.job} (exit {result.returncode})", file=sys.stderr)
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    history = History(path=Path(args.history_file))
    print(render_all_jobs(history, limit=args.limit))
    return 0


def cmd_concurrency(args: argparse.Namespace) -> int:
    cfg = concurrency_from_dict({
        "job_name": args.job,
        "max_slots": args.max_slots,
        "lock_dir": args.lock_dir,
    })
    print(render_concurrency_status(cfg))
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    return print_progress(Path(args.file))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "exec":
        return cmd_exec(args)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "concurrency":
        return cmd_concurrency(args)
    if args.command == "progress":
        returnparser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

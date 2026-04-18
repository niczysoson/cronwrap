"""Pre/post execution hooks for cron jobs."""
from __future__ import annotations
import subprocess
import logging
from dataclasses import dataclass, field
from typing import List, Optional

log = logging.getLogger(__name__)


@dataclass
class HookConfig:
    pre: List[str] = field(default_factory=list)
    post: List[str] = field(default_factory=list)
    post_failure: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    stop_on_pre_failure: bool = True

    def __post_init__(self):
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")


def hook_config_from_dict(d: dict) -> HookConfig:
    return HookConfig(
        pre=d.get("pre", []),
        post=d.get("post", []),
        post_failure=d.get("post_failure", []),
        timeout_seconds=int(d.get("timeout_seconds", 30)),
        stop_on_pre_failure=bool(d.get("stop_on_pre_failure", True)),
    )


@dataclass
class HookResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def _run_hook(cmd: str, timeout: int) -> HookResult:
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return HookResult(cmd, proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired:
        log.warning("Hook timed out: %s", cmd)
        return HookResult(cmd, -1, "", "timeout")
    except Exception as exc:  # pragma: no cover
        log.error("Hook error: %s: %s", cmd, exc)
        return HookResult(cmd, -1, "", str(exc))


def run_pre_hooks(cfg: HookConfig) -> List[HookResult]:
    results = []
    for cmd in cfg.pre:
        r = _run_hook(cmd, cfg.timeout_seconds)
        log.info("pre-hook %r -> %d", cmd, r.returncode)
        results.append(r)
        if not r.succeeded and cfg.stop_on_pre_failure:
            log.error("pre-hook failed, stopping: %s", cmd)
            break
    return results


def run_post_hooks(cfg: HookConfig, job_succeeded: bool) -> List[HookResult]:
    results = []
    cmds = cfg.post + ([] if job_succeeded else cfg.post_failure)
    for cmd in cmds:
        r = _run_hook(cmd, cfg.timeout_seconds)
        log.info("post-hook %r -> %d", cmd, r.returncode)
        results.append(r)
    return results

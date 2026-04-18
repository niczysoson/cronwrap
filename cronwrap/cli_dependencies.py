"""CLI helpers for dependency status rendering."""
from __future__ import annotations
from cronwrap.dependencies import DependencyConfig, DependencyResult, check_dependencies
from cronwrap.history import JobHistory


def render_dependency_status(result: DependencyResult) -> str:
    lines = []
    if result.satisfied:
        lines.append("\u2705  All dependencies satisfied.")
    else:
        lines.append("\u274c  Dependency check FAILED")
        for name in result.missing:
            lines.append(f"   - {name} has no recent success")
    return "\n".join(lines)


def check_and_exit_if_blocked(
    config: DependencyConfig,
    history: JobHistory,
) -> None:
    """Print status and raise SystemExit(1) if dependencies are not met."""
    result = check_dependencies(config, history)
    print(render_dependency_status(result))
    if not result.satisfied:
        raise SystemExit(1)

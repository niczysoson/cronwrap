"""CLI helpers for secret masking status."""
from __future__ import annotations
from typing import Optional
from cronwrap.secrets import MaskConfig


def render_mask_config(cfg: Optional[MaskConfig]) -> str:
    if cfg is None:
        return "Secret masking: disabled\n"
    lines = ["Secret masking: enabled"]
    if cfg.patterns:
        lines.append(f"  Regex patterns : {len(cfg.patterns)}")
        for p in cfg.patterns:
            lines.append(f"    - {p}")
    else:
        lines.append("  Regex patterns : none")
    if cfg.env_vars:
        lines.append(f"  Env var secrets: {len(cfg.env_vars)}")
        for v in cfg.env_vars:
            lines.append(f"    - {v}")
    else:
        lines.append("  Env var secrets: none")
    lines.append(f"  Placeholder    : {cfg.placeholder}")
    return "\n".join(lines) + "\n"


def apply_mask_to_result(stdout: str, stderr: str, cfg: Optional[MaskConfig]):
    """Return (masked_stdout, masked_stderr)."""
    from cronwrap.secrets import mask_output
    return mask_output(stdout, cfg), mask_output(stderr, cfg)

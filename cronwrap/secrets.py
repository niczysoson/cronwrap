"""Secret/sensitive value masking for logs and output."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MaskConfig:
    patterns: List[str] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)
    placeholder: str = "***"

    def __post_init__(self):
        if not self.placeholder:
            raise ValueError("placeholder must not be empty")


def mask_config_from_dict(d: dict) -> MaskConfig:
    return MaskConfig(
        patterns=d.get("patterns", []),
        env_vars=d.get("env_vars", []),
        placeholder=d.get("placeholder", "***"),
    )


def _collect_secrets(cfg: MaskConfig) -> List[str]:
    secrets: List[str] = []
    for var in cfg.env_vars:
        val = os.environ.get(var)
        if val:
            secrets.append(val)
    return secrets


def mask_text(text: str, cfg: MaskConfig) -> str:
    result = text
    for pat in cfg.patterns:
        result = re.sub(pat, cfg.placeholder, result)
    for secret in _collect_secrets(cfg):
        result = result.replace(secret, cfg.placeholder)
    return result


def mask_command(cmd: str, cfg: Optional[MaskConfig]) -> str:
    if cfg is None:
        return cmd
    return mask_text(cmd, cfg)


def mask_output(output: str, cfg: Optional[MaskConfig]) -> str:
    if cfg is None:
        return output
    return mask_text(output, cfg)

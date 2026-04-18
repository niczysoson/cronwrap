"""Truncate command output to a configurable maximum length."""
from __future__ import annotations
from dataclasses import dataclass, field


_DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB
_TRUNCATION_NOTICE = "\n... [output truncated] ..."


@dataclass
class OutputLimitConfig:
    max_bytes: int = _DEFAULT_MAX_BYTES
    truncation_notice: str = _TRUNCATION_NOTICE

    def __post_init__(self) -> None:
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be at least 1")

    def is_limited(self, text: str) -> bool:
        return len(text.encode()) > self.max_bytes

    def apply(self, text: str) -> str:
        """Return text truncated to max_bytes with a notice appended if needed."""
        encoded = text.encode()
        if len(encoded) <= self.max_bytes:
            return text
        truncated = encoded[: self.max_bytes].decode(errors="ignore")
        return truncated + self.truncation_notice


def output_limit_from_dict(d: dict) -> OutputLimitConfig:
    """Build an OutputLimitConfig from a plain dict (e.g. parsed YAML/JSON)."""
    kwargs: dict = {}
    if "max_bytes" in d:
        kwargs["max_bytes"] = int(d["max_bytes"])
    if "truncation_notice" in d:
        kwargs["truncation_notice"] = str(d["truncation_notice"])
    return OutputLimitConfig(**kwargs)


def apply_output_limit(text: str, cfg: OutputLimitConfig | None) -> str:
    """Convenience wrapper — returns text unchanged when cfg is None."""
    if cfg is None:
        return text
    return cfg.apply(text)

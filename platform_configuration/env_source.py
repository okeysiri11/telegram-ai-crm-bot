# Environment source — ONLY module allowed to read process environment / .env files.

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_environment(*, dotenv_path: str | Path | None = None) -> dict[str, str]:
    """Load .env once and return a snapshot of os.environ (string values only)."""
    path = Path(dotenv_path) if dotenv_path else _project_root() / ".env"
    if path.is_file():
        load_dotenv(path, override=False)
    return {key: value for key, value in os.environ.items() if isinstance(value, str)}


def getenv(name: str, default: str = "") -> str:
    load_environment()
    value = os.environ.get(name, default)
    return value.strip() if isinstance(value, str) else str(default).strip()


def getenv_bool(name: str, default: bool = False) -> bool:
    raw = getenv(name, "")
    if not raw:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def getenv_int(name: str, default: int) -> int:
    raw = getenv(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def getenv_float(name: str, default: float) -> float:
    raw = getenv(name, "")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def optional_telegram_id(name: str) -> int | None:
    raw = getenv(name, "")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def env_snapshot_redacted() -> dict[str, str]:
    """Return env keys with secrets redacted (for diagnostics)."""
    secret_markers = ("SECRET", "TOKEN", "PASSWORD", "KEY", "DSN")
    out: dict[str, str] = {}
    for key, value in load_environment().items():
        if any(marker in key.upper() for marker in secret_markers):
            out[key] = "***" if value else ""
        else:
            out[key] = value
    return out

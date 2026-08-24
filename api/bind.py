"""Listen address helpers — honor platform PORT without breaking local 8080."""

from __future__ import annotations

import os


def resolve_api_port(default: int = 8080) -> int:
    raw = (os.environ.get("API_PORT") or os.environ.get("PORT") or "").strip()
    if raw:
        try:
            value = int(raw)
            if 1 <= value <= 65535:
                return value
        except ValueError:
            pass
    return default


def resolve_api_host(default: str = "127.0.0.1") -> str:
    return (os.environ.get("API_HOST") or default).strip() or default


def client_max_size_bytes(default_mb: int = 32) -> int:
    raw = (os.environ.get("ADOS_MAX_UPLOAD_MB") or str(default_mb)).strip()
    try:
        mb = int(raw)
    except ValueError:
        mb = default_mb
    return max(1, mb) * 1024 * 1024

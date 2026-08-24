"""URL validation / SSRF guards for Legal Ops manual watch sources — Lawyer 3.4.

Server does NOT fetch arbitrary user URLs by default.
If a fetch is ever enabled, call assert_safe_public_https_url first.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "169.254.169.254",
}


def validate_source_url(url: str | None, *, allow_empty: bool = True) -> dict[str, Any]:
    """Validate user-provided source URL. Does not perform network I/O."""
    raw = (url or "").strip()
    if not raw:
        if allow_empty:
            return {"ok": True, "url": None, "message_ru": None}
        return {"ok": False, "error": "validation", "message_ru": "Укажите URL источника"}
    if len(raw) > 2048:
        return {"ok": False, "error": "validation", "message_ru": "URL слишком длинный"}
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return {"ok": False, "error": "validation", "message_ru": "Разрешены только http/https URL"}
    if parsed.scheme != "https":
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Для источника мониторинга требуется HTTPS URL",
        }
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        return {"ok": False, "error": "validation", "message_ru": "Некорректный hostname в URL"}
    if host in BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        return {"ok": False, "error": "ssrf", "message_ru": "URL указывает на запрещённый хост"}
    # Literal IP
    try:
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return {"ok": False, "error": "ssrf", "message_ru": "URL указывает на частный/локальный адрес"}
    except ValueError:
        pass
    return {"ok": True, "url": raw, "host": host, "message_ru": None}


def assert_safe_public_https_url(url: str) -> str:
    """Raise ValueError if URL is unsafe for server-side fetch."""
    checked = validate_source_url(url, allow_empty=False)
    if not checked.get("ok"):
        raise ValueError(checked.get("message_ru") or "unsafe url")
    host = checked["host"]
    # Resolve DNS and re-check (best-effort SSRF)
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolve failed: {exc}") from exc
    for info in infos:
        addr = info[4][0]
        ip = ipaddress.ip_address(addr)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("URL resolves to non-public address")
    return checked["url"]


# Explicit: production monitoring must not scrape user URLs without a designed provider.
FETCH_USER_URLS = False

"""Outbound HTTP for Recruiting providers. Secrets never logged or returned."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from services.recruiting_ops.provider_errors import classify_http_error, safe_error_message

DEFAULT_TIMEOUT = 12
MAX_ATTEMPTS = 4
Transport = Callable[[str, str, dict[str, str], bytes | None, float], dict[str, Any]]

_TRANSPORT: Transport | None = None


def set_http_transport(transport: Transport | None) -> None:
    global _TRANSPORT
    _TRANSPORT = transport


def reset_http_transport() -> None:
    set_http_transport(None)


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    out = {}
    for key, value in headers.items():
        lowered = key.lower()
        if lowered in {"authorization", "access-token", "developer-token", "x-goog-api-key"}:
            out[key] = "present" if value else "missing"
        else:
            out[key] = value
    return out


def _default_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            text = raw.decode("utf-8", errors="replace")
            parsed: Any = None
            try:
                parsed = json.loads(text) if text else None
            except json.JSONDecodeError:
                parsed = None
            return {"status": int(response.status), "text": text, "json": parsed, "ok": 200 <= int(response.status) < 300}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", errors="replace") if raw else str(exc)
        parsed = None
        try:
            parsed = json.loads(text) if text else None
        except json.JSONDecodeError:
            parsed = None
        return {"status": int(exc.code), "text": text, "json": parsed, "ok": False}
    except Exception as exc:
        return {"status": 0, "text": type(exc).__name__, "json": None, "ok": False}


def backoff_seconds(attempt: int) -> int:
    return min(60, 2 ** max(1, attempt))


def provider_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    form: dict[str, str] | None = None,
    query: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    attempts: int = 1,
) -> dict[str, Any]:
    started = time.perf_counter()
    hdrs = dict(headers or {})
    payload: bytes | None = None
    if json_body is not None:
        payload = json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    elif form is not None:
        payload = urllib.parse.urlencode(form).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    target = url
    if query:
        encoded = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        target = f"{url}{'&' if '?' in url else '?'}{encoded}"
    last: dict[str, Any] = {}
    tries = max(1, min(int(attempts), MAX_ATTEMPTS))
    for attempt in range(1, tries + 1):
        transport = _TRANSPORT or _default_transport
        last = transport(method.upper(), target, hdrs, payload, timeout)
        status = int(last.get("status") or 0)
        if last.get("ok") or status not in {429, 500, 502, 503, 0}:
            break
        if attempt < tries and status in {429, 500, 502, 503, 0}:
            time.sleep(min(0.05, backoff_seconds(attempt) / 100) if _TRANSPORT else min(1.0, backoff_seconds(attempt) / 10))
    latency = int((time.perf_counter() - started) * 1000)
    ok = bool(last.get("ok"))
    error_code = None if ok else classify_http_error(last.get("status"), last.get("json") or last.get("text"))
    return {
        "ok": ok,
        "status": last.get("status"),
        "json": last.get("json"),
        "text": None if ok else (str(last.get("text") or "")[:240] or None),
        "latency_ms": latency,
        "error": error_code,
        "error_code": error_code,
        "message_ru": None if ok else safe_error_message(error_code or ""),
        "request": {"method": method.upper(), "host": urllib.parse.urlparse(target).netloc, "headers": _redact_headers(hdrs)},
        "fake_data": False,
        "live": _TRANSPORT is None,
        "mocked_http": _TRANSPORT is not None,
    }

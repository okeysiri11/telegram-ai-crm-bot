"""HMAC auth for Vanguard → Recruiting ingest. Secret stays on the server."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime

REPLAY_WINDOW_SECONDS = 300
DEV_FALLBACK_SECRET = "vanguard-dev-ingest-secret"

_seen_nonces: dict[str, float] = {}


def reset_ingest_auth_for_tests() -> None:
    _seen_nonces.clear()


def resolve_ingest_secret() -> str | None:
    secret = (os.getenv("VANGUARD_INGEST_SECRET") or "").strip()
    if secret:
        return secret
    if is_production_runtime():
        return None
    return (os.getenv("VANGUARD_DEV_INGEST_SECRET") or DEV_FALLBACK_SECRET).strip() or None


def sign_ingest_body(*, body: bytes | str, timestamp: str, nonce: str, secret: str | None = None) -> str:
    key = secret if secret is not None else resolve_ingest_secret()
    if not key:
        raise RuntimeError("vanguard ingest secret is not configured")
    raw = body.encode("utf-8") if isinstance(body, str) else body
    msg = f"{timestamp}.{nonce}.".encode("utf-8") + raw
    return hmac.new(key.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_ingest_request(
    *,
    body: bytes | str,
    signature: str | None,
    timestamp: str | None,
    nonce: str | None,
    now: float | None = None,
) -> dict[str, Any]:
    secret = resolve_ingest_secret()
    if not secret:
        return {
            "ok": False,
            "error": "ingest_not_configured",
            "message_ru": "Vanguard ingest secret не настроен на сервере.",
        }
    if not signature or not str(signature).strip():
        return {
            "ok": False,
            "error": "missing_signature",
            "message_ru": "Подпись запроса отсутствует.",
        }
    if not timestamp or not nonce:
        return {
            "ok": False,
            "error": "missing_signature",
            "message_ru": "Нужны заголовки X-Vanguard-Timestamp и X-Vanguard-Nonce.",
        }
    try:
        ts = float(timestamp)
    except (TypeError, ValueError):
        return {"ok": False, "error": "expired_signature", "message_ru": "Некорректная метка времени."}
    current = time.time() if now is None else now
    if abs(current - ts) > REPLAY_WINDOW_SECONDS:
        return {
            "ok": False,
            "error": "expired_signature",
            "message_ru": "Подпись истекла.",
        }
    if nonce in _seen_nonces:
        return {
            "ok": False,
            "error": "bad_signature",
            "message_ru": "Повтор nonce — запрос отклонён.",
        }
    expected = sign_ingest_body(body=body, timestamp=str(timestamp), nonce=str(nonce), secret=secret)
    provided = str(signature).removeprefix("sha256=").strip()
    if not hmac.compare_digest(expected, provided):
        return {
            "ok": False,
            "error": "bad_signature",
            "message_ru": "Неверная подпись запроса.",
        }
    _seen_nonces[str(nonce)] = current
    cutoff = current - REPLAY_WINDOW_SECONDS * 2
    stale = [k for k, seen in _seen_nonces.items() if seen < cutoff]
    for key in stale:
        _seen_nonces.pop(key, None)
    return {"ok": True}

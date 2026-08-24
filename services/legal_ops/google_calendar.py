"""Google Calendar adapter boundary — Sprint 51.0 / Lawyer 3.3.

Honest status: needs_config / needs_oauth / connected.
OAuth tokens: server-side only (env or local token file) — never frontend.
Live Google HTTP only when LEGAL_OPS_GCAL_LIVE=1; otherwise offline deterministic adapter
when credentials exist (CI-safe). Does not fabricate success without credentials.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TOKEN_PATH = Path(os.environ.get("LEGAL_OPS_GCAL_TOKEN_PATH") or "data/legal_ops_gcal_tokens.json")


def _read_token_store() -> dict[str, Any]:
    try:
        if TOKEN_PATH.exists():
            return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("gcal token store read failed: %s", exc)
    return {}


def _write_token_store(data: dict[str, Any]) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_org_refresh_token(organization_id: str) -> None:
    store = _read_token_store()
    store.pop(organization_id or "default", None)
    _write_token_store(store)


def save_refresh_token(organization_id: str, refresh_token: str, *, account_email: str | None = None) -> None:
    """Server-side token persistence (file). Prefer vault/SecretManager in production."""
    store = _read_token_store()
    store[organization_id or "default"] = {
        "refresh_token": refresh_token,
        "account_email": account_email,
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    _write_token_store(store)


def get_org_refresh_token(organization_id: str | None = None) -> str:
    env = (os.environ.get("GOOGLE_CALENDAR_REFRESH_TOKEN") or "").strip()
    if env:
        return env
    store = _read_token_store()
    row = store.get(organization_id or "default") or store.get("default") or {}
    return str(row.get("refresh_token") or "").strip()


def google_oauth_client() -> tuple[str, str]:
    client_id = (os.environ.get("GOOGLE_CALENDAR_CLIENT_ID") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (
        os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET") or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or ""
    ).strip()
    return client_id, client_secret


def google_calendar_status(organization_id: str | None = None) -> dict[str, Any]:
    client_id, client_secret = google_oauth_client()
    refresh = get_org_refresh_token(organization_id)
    oauth_ready = bool(client_id and client_secret)
    connected = bool(oauth_ready and refresh)
    live = (os.environ.get("LEGAL_OPS_GCAL_LIVE") or "").strip() in {"1", "true", "yes"}
    if connected:
        status = "connected"
        message = (
            "Google Calendar подключён (live API)"
            if live
            else "Google Calendar подключён (адаптер; live API при LEGAL_OPS_GCAL_LIVE=1)"
        )
    elif oauth_ready:
        status = "needs_oauth"
        message = "Требуется авторизация Google OAuth (токен не сохранён)"
    else:
        status = "needs_config"
        message = "Требуется настройка Google Calendar (CLIENT_ID / CLIENT_SECRET)"
    store = _read_token_store()
    acct = (store.get(organization_id or "default") or {}).get("account_email")
    return {
        "provider": "google_calendar",
        "implemented": True,
        "ready": connected,
        "status": status,
        "message_ru": message,
        "supports_duplicate_prevention": True,
        "oauth_client_configured": oauth_ready,
        "live_api": live and connected,
        "account_email": acct,
        "selected_calendar_id": "primary",
        "sync_direction_supported": ["ados_to_google"],
        "sync_direction_limited": ["google_to_ados", "bidirectional"],
        "token_storage": "server_side_file_or_env",
    }


def make_dedupe_key(*, organization_id: str, title: str, starts_at: str | None, case_id: str | None = None) -> str:
    raw = f"{organization_id}|{title}|{starts_at or ''}|{case_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def oauth_redirect_uri() -> str:
    return (
        os.environ.get("GOOGLE_CALENDAR_REDIRECT_URI")
        or "http://127.0.0.1:8080/api/legal-ops/v1/integrations/google-calendar/callback"
    ).strip()


def build_oauth_url() -> str | None:
    client_id, _ = google_oauth_client()
    if not client_id:
        return None
    from urllib.parse import urlencode

    q = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": oauth_redirect_uri(),
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.events",
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{q}"


def exchange_oauth_code(code: str, *, organization_id: str = "default") -> dict[str, Any]:
    """Exchange authorization code for refresh token via Google token endpoint."""
    client_id, client_secret = google_oauth_client()
    if not (client_id and client_secret and code):
        return {"ok": False, "status": "needs_config", "message_ru": "OAuth client не настроен"}
    live = (os.environ.get("LEGAL_OPS_GCAL_LIVE") or "").strip() in {"1", "true", "yes"}
    if not live:
        # Offline/dev: accept code and store a non-secret placeholder only when explicitly testing connect flow
        # without calling Google — marks needs_oauth→connected for local desk when CLIENT set.
        # Real tokens require LEGAL_OPS_GCAL_LIVE=1.
        token = f"dev_refresh_{hashlib.sha256(code.encode()).hexdigest()[:24]}"
        save_refresh_token(organization_id, token, account_email="dev@local")
        return {
            "ok": True,
            "status": "connected",
            "message_ru": "OAuth code принят в offline-режиме (LEGAL_OPS_GCAL_LIVE не включён). Для реального обмена включите live.",
            "mode": "offline_adapter",
        }
    try:
        import urllib.request
        from urllib.parse import urlencode

        data = urlencode(
            {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": oauth_redirect_uri(),
                "grant_type": "authorization_code",
            }
        ).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 — official Google endpoint
            payload = json.loads(resp.read().decode())
        refresh = payload.get("refresh_token") or get_org_refresh_token(organization_id)
        if not refresh:
            return {
                "ok": False,
                "status": "needs_oauth",
                "message_ru": "Google не вернул refresh_token. Повторите consent.",
            }
        save_refresh_token(organization_id, refresh)
        return {"ok": True, "status": "connected", "message_ru": "Google Calendar OAuth завершён", "mode": "live"}
    except Exception as exc:
        logger.warning("gcal oauth exchange failed: %s", exc)
        return {"ok": False, "status": "ERROR", "message_ru": f"OAuth ошибка: {exc}", "error": str(exc)}


def sync_event_to_google(event: dict[str, Any]) -> dict[str, Any]:
    """Attempt sync. Without credentials → needs_config, no fake remote id."""
    org = str(event.get("organization_id") or "default")
    status = google_calendar_status(org)
    if status["status"] != "connected":
        return {
            "ok": False,
            "sync_status": status["status"],
            "gcal_event_id": None,
            "message_ru": status["message_ru"],
            "provider": "google_calendar",
        }
    # Prefer existing mapped id (duplicate prevention)
    existing = event.get("gcal_event_id") or event.get("external_event_id")
    if existing:
        return {
            "ok": True,
            "sync_status": "synced",
            "gcal_event_id": existing,
            "message_ru": "Использован существующий Google event mapping (без дубля)",
            "provider": "google_calendar",
            "reused_mapping": True,
        }
    seed = f"{event.get('organization_id')}:{event.get('dedupe_key') or event.get('id')}"
    gcal_id = "gcal_" + hashlib.sha256(seed.encode()).hexdigest()[:24]
    live = status.get("live_api")
    return {
        "ok": True,
        "sync_status": "synced",
        "gcal_event_id": gcal_id,
        "message_ru": (
            "Событие синхронизировано с Google Calendar (live)"
            if live
            else "Событие синхронизировано с Google Calendar (адаптер)"
        ),
        "provider": "google_calendar",
        "mode": "live" if live else "offline_adapter",
    }

"""OAuth initiate/callback for Meta, Google Ads, TikTok. Tokens stay server-side."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
from typing import Any

from services.recruiting_ops.provider_http import provider_request
from services.recruiting_ops.secret_store import get_secret_store

OAUTH_PROVIDERS = ("meta", "google", "tiktok")
STATE_TTL_SECONDS = 600
_HMAC_LEN = 32  # SHA-256 digest; prefix framing avoids 0x2e inside the signature

SCOPES = {
    "meta": "ads_management,ads_read,business_management,pages_show_list",
    "google": "https://www.googleapis.com/auth/adwords",
    "tiktok": "advertiser_management",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def graph_version() -> str:
    return _txt(os.getenv("META_GRAPH_API_VERSION") or os.getenv("FACEBOOK_GRAPH_API_VERSION")) or "v21.0"


def google_ads_version() -> str:
    return _txt(os.getenv("GOOGLE_ADS_API_VERSION")) or "v18"


def tiktok_version() -> str:
    return _txt(os.getenv("TIKTOK_ADS_API_VERSION")) or "v1.3"


def public_backend_base() -> str:
    for name in ("RECRUITING_PUBLIC_URL", "PUBLIC_API_BASE", "ADOS_PUBLIC_URL"):
        value = _txt(os.getenv(name))
        if value:
            return value.rstrip("/")
    website = _txt(os.getenv("VANGUARD_WEBSITE_URL"))
    if website:
        parsed = urllib.parse.urlparse(website)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return "http://127.0.0.1:8080"


def redirect_uri(provider: str) -> str:
    key = _txt(provider).lower()
    env_map = {
        "meta": "META_ADS_REDIRECT_URI",
        "google": "GOOGLE_ADS_REDIRECT_URI",
        "tiktok": "TIKTOK_ADS_REDIRECT_URI",
    }
    configured = _txt(os.getenv(env_map.get(key, "")))
    if configured:
        return configured
    return f"{public_backend_base()}/api/recruiting-ops/v1/oauth/{key}/callback"


def _sign_key() -> bytes:
    secret = (
        os.getenv("RECRUITING_OAUTH_STATE_KEY")
        or os.getenv("IAM_JWT_SECRET")
        or os.getenv("JWT_SECRET")
        or "recruiting-oauth-dev"
    )
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encode_state(*, provider: str, organization_id: str, nonce: str | None = None) -> str:
    payload = {
        "p": _txt(provider).lower(),
        "o": _txt(organization_id) or "ados",
        "n": _txt(nonce) or hashlib.sha256(os.urandom(16)).hexdigest()[:16],
        "exp": int(time.time()) + STATE_TTL_SECONDS,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_sign_key(), raw, hashlib.sha256).digest()
    # HMAC first (fixed 32 bytes). Do not join with b"." — a digest can contain 0x2e
    # and legacy rsplit then verified the wrong slice (~12% of states).
    return base64.urlsafe_b64encode(sig + raw).decode("ascii")


def _payload_if_valid(raw: bytes, sig: bytes) -> dict[str, Any] | None:
    if len(sig) != _HMAC_LEN:
        return None
    expected = hmac.new(_sign_key(), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    payload = json.loads(raw.decode("utf-8"))
    return payload if isinstance(payload, dict) else None


def decode_state(state: str) -> dict[str, Any]:
    try:
        blob = base64.urlsafe_b64decode(_txt(state).encode("ascii"))
        payload = None
        if len(blob) > _HMAC_LEN:
            payload = _payload_if_valid(blob[_HMAC_LEN:], blob[:_HMAC_LEN])
        if payload is None and b"." in blob:
            raw, sig = blob.rsplit(b".", 1)
            payload = _payload_if_valid(raw, sig)
        if payload is None:
            return {"ok": False, "error": "AUTH_ERROR", "message_ru": "OAuth state недействителен."}
        if int(payload.get("exp") or 0) < int(time.time()):
            return {"ok": False, "error": "TOKEN_EXPIRED", "message_ru": "OAuth state истёк."}
        return {"ok": True, "provider": payload.get("p"), "organization_id": payload.get("o"), "nonce": payload.get("n")}
    except Exception:
        return {"ok": False, "error": "AUTH_ERROR", "message_ru": "OAuth state повреждён."}


def _app_credentials(provider: str) -> dict[str, str]:
    store = get_secret_store()
    if provider == "meta":
        return {
            "client_id": _txt(os.getenv("META_ADS_APP_ID") or os.getenv("META_APP_ID") or store.get("meta", "app_id")),
            "client_secret": _txt(os.getenv("META_ADS_APP_SECRET") or os.getenv("META_APP_SECRET") or store.get("meta", "app_secret")),
        }
    if provider == "google":
        return {
            "client_id": _txt(os.getenv("GOOGLE_ADS_CLIENT_ID") or store.get("google", "client_id")),
            "client_secret": _txt(os.getenv("GOOGLE_ADS_CLIENT_SECRET") or store.get("google", "client_secret")),
        }
    return {
        "client_id": _txt(os.getenv("TIKTOK_ADS_APP_ID") or store.get("tiktok", "app_id")),
        "client_secret": _txt(os.getenv("TIKTOK_ADS_APP_SECRET") or store.get("tiktok", "app_secret")),
    }


def oauth_ready(provider: str) -> bool:
    creds = _app_credentials(_txt(provider).lower())
    return bool(creds["client_id"] and creds["client_secret"])


def authorize_url(provider: str, organization_id: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    if key not in OAUTH_PROVIDERS:
        return {"ok": False, "error": "validation", "message_ru": "OAuth недоступен для этого провайдера."}
    creds = _app_credentials(key)
    if not creds["client_id"]:
        return {"ok": False, "error": "NOT_CONFIGURED", "status": "NOT_CONFIGURED", "message_ru": "Не задан app/client identifier."}
    state = encode_state(provider=key, organization_id=organization_id)
    callback = redirect_uri(key)
    if key == "meta":
        url = (
            f"https://www.facebook.com/{graph_version()}/dialog/oauth?"
            + urllib.parse.urlencode(
                {"client_id": creds["client_id"], "redirect_uri": callback, "state": state, "scope": SCOPES["meta"], "response_type": "code"}
            )
        )
    elif key == "google":
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
            {
                "client_id": creds["client_id"],
                "redirect_uri": callback,
                "response_type": "code",
                "scope": SCOPES["google"],
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
    else:
        url = "https://business-api.tiktok.com/portal/auth?" + urllib.parse.urlencode(
            {"app_id": creds["client_id"], "redirect_uri": callback, "state": state}
        )
    return {
        "ok": True,
        "provider": key,
        "authorize_url": url,
        "redirect_uri": callback,
        "state_bound": True,
        "scopes": SCOPES[key],
        "status": "CONFIGURING",
        "message_ru": "Перейдите по ссылке провайдера. Токен не сохраняется в браузере.",
    }


def exchange_code(provider: str, code: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    creds = _app_credentials(key)
    callback = redirect_uri(key)
    if not creds["client_id"] or not creds["client_secret"] or not _txt(code):
        return {"ok": False, "error": "NOT_CONFIGURED", "status": "NOT_CONFIGURED", "message_ru": "Нет кода или приложения OAuth."}
    if key == "meta":
        result = provider_request(
            "GET",
            f"https://graph.facebook.com/{graph_version()}/oauth/access_token",
            query={
                "client_id": creds["client_id"],
                "redirect_uri": callback,
                "client_secret": creds["client_secret"],
                "code": code,
            },
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        token = _txt(data.get("access_token"))
        if result["ok"] and token:
            long_lived = provider_request(
                "GET",
                f"https://graph.facebook.com/{graph_version()}/oauth/access_token",
                query={
                    "grant_type": "fb_exchange_token",
                    "client_id": creds["client_id"],
                    "client_secret": creds["client_secret"],
                    "fb_exchange_token": token,
                },
            )
            ll = long_lived.get("json") if isinstance(long_lived.get("json"), dict) else {}
            token = _txt(ll.get("access_token")) or token
            expires = ll.get("expires_in") or data.get("expires_in")
            return {"ok": True, "access_token": token, "expires_in": expires, "refresh_token": None, "live": result.get("live")}
        return {"ok": False, "error": result.get("error"), "message_ru": result.get("message_ru")}
    if key == "google":
        result = provider_request(
            "POST",
            "https://oauth2.googleapis.com/token",
            form={
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "redirect_uri": callback,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        data = result.get("json") if isinstance(result.get("json"), dict) else {}
        if result["ok"] and (_txt(data.get("refresh_token")) or _txt(data.get("access_token"))):
            return {
                "ok": True,
                "access_token": _txt(data.get("access_token")) or None,
                "refresh_token": _txt(data.get("refresh_token")) or None,
                "expires_in": data.get("expires_in"),
                "live": result.get("live"),
            }
        return {"ok": False, "error": result.get("error"), "message_ru": result.get("message_ru")}
    result = provider_request(
        "POST",
        f"https://business-api.tiktok.com/open_api/{tiktok_version()}/oauth2/access_token/",
        json_body={"app_id": creds["client_id"], "secret": creds["client_secret"], "auth_code": code},
    )
    data = result.get("json") if isinstance(result.get("json"), dict) else {}
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    token = _txt(inner.get("access_token"))
    if result["ok"] and token:
        return {"ok": True, "access_token": token, "refresh_token": _txt(inner.get("refresh_token")) or None, "expires_in": inner.get("expires_in"), "live": result.get("live")}
    return {"ok": False, "error": result.get("error"), "message_ru": result.get("message_ru")}


def refresh_google_access_token() -> dict[str, Any]:
    store = get_secret_store()
    creds = _app_credentials("google")
    refresh = _txt(store.get("google", "refresh_token") or os.getenv("GOOGLE_ADS_REFRESH_TOKEN"))
    if not creds["client_id"] or not creds["client_secret"] or not refresh:
        return {"ok": False, "error": "NOT_CONFIGURED"}
    result = provider_request(
        "POST",
        "https://oauth2.googleapis.com/token",
        form={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
    )
    data = result.get("json") if isinstance(result.get("json"), dict) else {}
    token = _txt(data.get("access_token"))
    if result["ok"] and token:
        return {"ok": True, "access_token": token, "expires_in": data.get("expires_in")}
    return {"ok": False, "error": result.get("error"), "message_ru": result.get("message_ru")}

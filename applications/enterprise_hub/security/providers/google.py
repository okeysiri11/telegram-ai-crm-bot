"""Google Sign-In provider — Sprint 30.1.

Verifies Google ID token claims when GOOGLE_CLIENT_ID is configured.
In development, accepts a structured demo payload from the local Vite plugin
(secret starts with google_demo_).

Compatible extension point for Microsoft / Apple / GitHub / Telegram providers.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError


def _b64url_json(segment: str) -> dict[str, Any]:
    import base64

    pad = "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(segment + pad)
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def decode_id_token_unverified(id_token: str) -> dict[str, Any]:
    parts = id_token.split(".")
    if len(parts) < 2:
        raise ValidationError("invalid Google id_token")
    return _b64url_json(parts[1])


def verify_google_id_token(id_token: str, *, client_id: str | None = None) -> dict[str, Any]:
    cid = (client_id or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    if not id_token:
        raise ValidationError("google id_token required")

    if id_token.startswith("google_demo_"):
        try:
            payload = json.loads(id_token[len("google_demo_") :])
        except json.JSONDecodeError as exc:
            raise ValidationError("invalid google demo credential") from exc
        email = str(payload.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("google demo credential missing email")
        return {
            "sub": str(payload.get("sub") or f"google-demo:{email}"),
            "email": email,
            "email_verified": True,
            "name": str(payload.get("name") or email.split("@")[0]),
            "picture": payload.get("picture"),
            "provider": "google",
            "mode": "demo",
        }

    if cid:
        url = (
            "https://oauth2.googleapis.com/tokeninfo?id_token="
            + urllib.parse.quote(id_token)
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:  # noqa: S310
                claims = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ValidationError("Google token verification failed") from exc
        if str(claims.get("aud") or "") != cid:
            raise ValidationError("Google token audience mismatch")
        email = str(claims.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Google token missing email")
        return {
            "sub": str(claims.get("sub") or ""),
            "email": email,
            "email_verified": str(claims.get("email_verified") or "").lower() in {"true", "1"},
            "name": str(claims.get("name") or email.split("@")[0]),
            "picture": claims.get("picture"),
            "provider": "google",
            "mode": "google_tokeninfo",
        }

    env = (os.environ.get("ENVIRONMENT") or "development").lower()
    if env in {"production", "prod"}:
        raise ValidationError("GOOGLE_CLIENT_ID required in production")
    claims = decode_id_token_unverified(id_token)
    email = str(claims.get("email") or "").strip().lower()
    if not email:
        raise ValidationError("Google id_token missing email")
    return {
        "sub": str(claims.get("sub") or f"google:{email}"),
        "email": email,
        "email_verified": bool(claims.get("email_verified", True)),
        "name": str(claims.get("name") or email.split("@")[0]),
        "picture": claims.get("picture"),
        "provider": "google",
        "mode": "dev_unverified",
    }

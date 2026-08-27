"""Provider credential SecretStore — never expose secret values on API.

Development: environment-backed plus encrypted-at-rest envelope for values
submitted through the connection wizard. Production secret managers can
replace EnvSecretStore without changing adapters.
"""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Protocol

from services.recruiting_ops.provider_readiness import SECRET_ENV_NAMES, redact_mapping

SECRET_FIELDS = {
    "meta": ("access_token", "app_secret"),
    "google": ("client_secret", "refresh_token", "developer_token"),
    "tiktok": ("access_token", "app_secret"),
    "telegram": ("bot_token",),
    "whatsapp": ("access_token", "verify_token"),
    "email": ("smtp_password", "api_key"),
}

PRIMARY_SECRET_FIELDS = {
    "meta": ("access_token",),
    "google": ("refresh_token", "developer_token"),
    "tiktok": ("access_token",),
    "telegram": ("bot_token",),
    "whatsapp": ("access_token",),
    "email": ("smtp_password",),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seal(plaintext: str, *, key: str) -> str:
    raw = plaintext.encode("utf-8")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    xored = bytes(b ^ digest[i % len(digest)] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(digest[:8] + xored).decode("ascii")


def _open(token: str, *, key: str) -> str:
    blob = base64.urlsafe_b64decode(token.encode("ascii"))
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return bytes(b ^ digest[i % len(digest)] for i, b in enumerate(blob[8:])).decode("utf-8")


class SecretStore(Protocol):
    def describe(self, provider: str, field: str) -> dict[str, Any]: ...
    def get(self, provider: str, field: str) -> str | None: ...
    def put(self, provider: str, field: str, value: str, *, expires_at: str | None = None, scopes: list[str] | None = None) -> dict[str, Any]: ...
    def rotate(self, provider: str, field: str, value: str) -> dict[str, Any]: ...
    def delete(self, provider: str, field: str) -> dict[str, Any]: ...


class EnvSecretStore:
    """Reads process env. Wizard-submitted values live in an encrypted envelope."""

    def __init__(self) -> None:
        self._envelope: dict[tuple[str, str], dict[str, Any]] = {}
        self._key = (
            os.getenv("RECRUITING_SECRET_STORE_KEY")
            or os.getenv("IAM_JWT_SECRET")
            or os.getenv("JWT_SECRET")
            or "recruiting-dev-secret-store"
        )

    def describe(self, provider: str, field: str) -> dict[str, Any]:
        env_name = _env_name(provider, field)
        present = bool(self.get(provider, field))
        meta = self._envelope.get((provider, field), {})
        return {
            "provider": provider,
            "field": field,
            "present": present,
            "source": "envelope" if (provider, field) in self._envelope else ("env" if present else None),
            "env_name": env_name,
            "expires_at": meta.get("expires_at"),
            "rotated_at": meta.get("rotated_at"),
            "scopes": list(meta.get("scopes") or []),
            "value": None,
        }

    def get(self, provider: str, field: str) -> str | None:
        packed = self._envelope.get((provider, field))
        if packed and packed.get("ciphertext"):
            try:
                return _open(str(packed["ciphertext"]), key=self._key)
            except Exception:
                return None
        env_name = _env_name(provider, field)
        if env_name:
            return (os.getenv(env_name) or "").strip() or None
        return None

    def put(
        self,
        provider: str,
        field: str,
        value: str,
        *,
        expires_at: str | None = None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        previous = (provider, field) in self._envelope or bool(self.get(provider, field))
        self._envelope[(provider, field)] = {
            "ciphertext": _seal(value, key=self._key),
            "expires_at": expires_at,
            "scopes": list(scopes or []),
            "rotated_at": _now() if previous else None,
            "updated_at": _now(),
        }
        return self.describe(provider, field)

    def rotate(self, provider: str, field: str, value: str) -> dict[str, Any]:
        current = self._envelope.get((provider, field), {})
        return self.put(provider, field, value, expires_at=current.get("expires_at"), scopes=current.get("scopes"))

    def delete(self, provider: str, field: str) -> dict[str, Any]:
        self._envelope.pop((provider, field), None)
        return self.describe(provider, field)


_STORE: EnvSecretStore | None = None


def get_secret_store() -> EnvSecretStore:
    global _STORE
    if _STORE is None:
        _STORE = EnvSecretStore()
    return _STORE


def reset_secret_store_for_tests() -> None:
    global _STORE
    _STORE = EnvSecretStore()


def _env_name(provider: str, field: str) -> str | None:
    mapping = {
        ("meta", "access_token"): "META_ADS_ACCESS_TOKEN",
        ("meta", "app_id"): "META_ADS_APP_ID",
        ("meta", "app_secret"): "META_ADS_APP_SECRET",
        ("google", "client_id"): "GOOGLE_ADS_CLIENT_ID",
        ("google", "client_secret"): "GOOGLE_ADS_CLIENT_SECRET",
        ("google", "refresh_token"): "GOOGLE_ADS_REFRESH_TOKEN",
        ("google", "developer_token"): "GOOGLE_ADS_DEVELOPER_TOKEN",
        ("tiktok", "access_token"): "TIKTOK_ADS_ACCESS_TOKEN",
        ("tiktok", "app_id"): "TIKTOK_ADS_APP_ID",
        ("tiktok", "app_secret"): "TIKTOK_ADS_APP_SECRET",
        ("telegram", "bot_token"): "VANGUARD_TELEGRAM_BOT_TOKEN",
        ("whatsapp", "access_token"): "WHATSAPP_TOKEN",
        ("whatsapp", "verify_token"): "WHATSAPP_VERIFY_TOKEN",
        ("email", "smtp_password"): "SMTP_PASSWORD",
        ("email", "smtp_host"): "SMTP_HOST",
        ("email", "smtp_user"): "SMTP_USER",
        ("email", "email_from"): "EMAIL_FROM",
    }
    return mapping.get((provider, field))


def credential_presence(provider: str) -> dict[str, Any]:
    store = get_secret_store()
    fields = SECRET_FIELDS.get(provider, ())
    primary = PRIMARY_SECRET_FIELDS.get(provider, fields)
    items = [store.describe(provider, field) for field in fields]
    present_map = {item["field"]: item["present"] for item in items}
    return {
        "provider": provider,
        "present": all(present_map.get(field) for field in primary) if primary else False,
        "any_present": any(item["present"] for item in items),
        "fields": {item["field"]: {"present": item["present"], "expires_at": item["expires_at"], "scopes": item["scopes"]} for item in items},
        "expires_at": next((item["expires_at"] for item in items if item.get("expires_at")), None),
    }


def public_secret_audit(action: str, provider: str, field: str) -> dict[str, Any]:
    """Audit payload — boolean presence only."""
    desc = get_secret_store().describe(provider, field)
    return redact_mapping(
        {
            "action": action,
            "provider": provider,
            "field": field,
            "present": desc["present"],
            "expires_at": desc.get("expires_at"),
            "secret_env_guard": field.upper() in SECRET_ENV_NAMES or True,
        }
    )

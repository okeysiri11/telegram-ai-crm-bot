"""Identity providers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import AUTH_METHODS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def authenticate_provider(
    store: EnterpriseHubStore,
    *,
    provider: str,
    subject: str,
    secret: str = "",
) -> dict[str, Any]:
    p = provider.lower().strip()
    # map provider names to auth method labels
    mapping = {
        "local": "password",
        "ldap": "ldap",
        "oauth2": "oauth2",
        "oidc": "oidc",
        "saml": "oauth2",
        "jwt": "jwt",
    }
    method = mapping.get(p, p)
    if method not in AUTH_METHODS and p not in ("local", "saml"):
        raise ValidationError(f"unsupported provider: {provider}")
    if not subject:
        raise ValidationError("subject required")
    aid = _id("isam_authn")
    return store.isam_auth_events.save(
        aid,
        {
            "auth_id": aid,
            "provider": p,
            "method": method if method in AUTH_METHODS else "password",
            "subject": subject,
            "success": True,
            "at": _now(),
        },
    )

"""Branding engine — logo, colors, domain, theme, locale, regional settings."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import BRANDING_KEYS
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BrandingEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def apply(
        self,
        *,
        tenant_id: str,
        logo: str | None = None,
        colors: dict[str, str] | None = None,
        domain: str | None = None,
        theme: str = "light",
        language: str = "en",
        timezone: str = "UTC",
        currency: str = "USD",
        locale: str = "en-US",
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        bid = _id("tn_br")
        payload = {
            "branding_id": bid,
            "tenant_id": tenant_id,
            "logo": logo or "",
            "colors": colors or {"primary": "#0B3D91", "accent": "#1E88E5"},
            "domain": domain or f"{tenant_id}.bidex.app",
            "theme": theme,
            "language": language,
            "timezone": timezone,
            "currency": currency,
            "locale": locale,
            "keys": list(BRANDING_KEYS),
            "updated_at": _now(),
        }
        return self.store.tn_branding.save(bid, payload)

    def localize(self, *, tenant_id: str, language: str, locale: str) -> dict[str, Any]:
        if not language:
            raise ValidationError("language is required")
        return self.apply(tenant_id=tenant_id, language=language, locale=locale)

    def status(self) -> dict[str, Any]:
        return {"branding_profiles": self.store.tn_branding.count(), "keys": list(BRANDING_KEYS)}

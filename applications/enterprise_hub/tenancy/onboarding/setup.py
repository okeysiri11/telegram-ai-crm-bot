"""Tenant onboarding setup wizard."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.branding import BrandingEngine
from applications.enterprise_hub.tenancy.licensing import LicenseManager
from applications.enterprise_hub.tenancy.provisioning import ProvisioningEngine
from applications.enterprise_hub.tenancy.tenant_manager import TenantManager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OnboardingSetup:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantManager(self.store)
        self.provisioning = ProvisioningEngine(self.store)
        self.licensing = LicenseManager(self.store)
        self.branding = BrandingEngine(self.store)

    def run(
        self,
        *,
        name: str,
        license_tier: str = "business",
        language: str = "en",
        currency: str = "USD",
    ) -> dict[str, Any]:
        tenant = self.tenants.create_tenant(name=name, license_tier=license_tier)
        license_rec = self.licensing.assign(tenant_id=tenant["tenant_id"], tier=license_tier)
        brand = self.branding.apply(
            tenant_id=tenant["tenant_id"], language=language, currency=currency
        )
        provision = self.provisioning.provision(tenant_id=tenant["tenant_id"])
        sid = _id("tn_setup")
        return self.store.tn_onboarding.save(
            sid,
            {
                "setup_id": sid,
                "tenant_id": tenant["tenant_id"],
                "license_id": license_rec["license_id"],
                "branding_id": brand["branding_id"],
                "provision_id": provision["provision_id"],
                "status": "complete",
                "at": _now(),
            },
        )

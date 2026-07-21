# Administration — platform/org/app/agent admin, licenses, feature flags.

from __future__ import annotations

import time
from typing import Any

from ecosystem.governance.audit.service import AuditService, audit_service
from ecosystem.governance.models import FeatureFlag, LicenseRecord
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class AdministrationService:
    def __init__(self, store: EcosystemStore | None = None, audit: AuditService | None = None) -> None:
        self._store = store or ecosystem_store
        self.audit = audit or audit_service
        self._seed_flags()

    def _seed_flags(self) -> None:
        if self._store.feature_flags.count() > 0:
            return
        for name, enabled, desc in [
            ("continuous_auditing", True, "Enable continuous compliance audits"),
            ("executive_governance", True, "Route governance to Executive AI"),
            ("optimization_hooks", True, "Apply optimization recommendations to policies"),
            ("beta_plugins", False, "Allow beta plugin lifecycle"),
        ]:
            flag = FeatureFlag(name=name, enabled=enabled, description=desc)
            self._store.feature_flags.save(flag.flag_id, flag)

    def _ensure_flags(self) -> None:
        if self._store.feature_flags.count() == 0:
            self._seed_flags()

    def platform_overview(self) -> dict[str, Any]:
        from ecosystem.config import DEFAULT_CONFIG

        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "governance_layer": DEFAULT_CONFIG.governance_layer,
            "compliance_layer": DEFAULT_CONFIG.compliance_layer,
            "applications": list(DEFAULT_CONFIG.registered_applications),
            "policies": self._store.policies.count(),
            "lifecycle_records": self._store.lifecycle_records.count(),
            "open_risks": len([r for r in self._store.risk_items.list_all() if r.status == "open"]),
            "feature_flags": len(self.list_flags()),
            "licenses": self._store.licenses.count(),
        }

    def organization_admin(self, organization_id: str) -> dict[str, Any]:
        licenses = [l for l in self._store.licenses.list_all() if l.organization_id == organization_id]
        return {
            "organization_id": organization_id,
            "licenses": [l.to_dict() for l in licenses],
            "members": self._store.memberships.count(),
        }

    def application_admin(self, application_id: str) -> dict[str, Any]:
        lifecycle = [r for r in self._store.lifecycle_records.list_all() if r.entity_id == application_id]
        return {
            "application_id": application_id,
            "lifecycle": [r.to_dict() for r in lifecycle],
            "catalog": [c.to_dict() for c in self._store.catalog_entries.list_all() if c.name == application_id],
        }

    def agent_admin(self) -> dict[str, Any]:
        return {
            "executives": self._store.executives.count(),
            "specialists": self._store.specialists.count(),
            "agent_lifecycle": [
                r.to_dict()
                for r in self._store.lifecycle_records.list_all()
                if r.kind.value == "agent"
            ],
        }

    def create_license(
        self,
        organization_id: str,
        *,
        plan: str = "standard",
        seats: int = 10,
        features: list[str] | None = None,
        expires_in_days: int = 365,
    ) -> LicenseRecord:
        if not organization_id:
            raise ValidationError("organization_id is required")
        license_rec = LicenseRecord(
            organization_id=organization_id,
            plan=plan,
            seats=seats,
            features=features or ["core", "assistant", "workforce"],
            expires_at=time.time() + expires_in_days * 86400,
        )
        self._store.licenses.save(license_rec.license_id, license_rec)
        self.audit.record("license_created", resource_type="license", resource_id=license_rec.license_id)
        return license_rec

    def list_licenses(self) -> list[LicenseRecord]:
        return self._store.licenses.list_all()

    def set_feature_flag(self, name: str, enabled: bool, *, description: str = "") -> FeatureFlag:
        self._ensure_flags()
        for flag in self._store.feature_flags.list_all():
            if flag.name == name:
                flag.enabled = enabled
                if description:
                    flag.description = description
                self._store.feature_flags.save(flag.flag_id, flag)
                self.audit.record("feature_flag_updated", resource_type="feature_flag", resource_id=flag.flag_id)
                return flag
        flag = FeatureFlag(name=name, enabled=enabled, description=description)
        self._store.feature_flags.save(flag.flag_id, flag)
        return flag

    def list_flags(self) -> list[FeatureFlag]:
        self._ensure_flags()
        return self._store.feature_flags.list_all()

    def is_enabled(self, name: str) -> bool:
        for flag in self.list_flags():
            if flag.name == name:
                return flag.enabled
        return False


administration_service = AdministrationService()

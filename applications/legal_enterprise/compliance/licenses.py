"""Licenses, permits, certificates — expiration and renewal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LicenseManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register_license(
        self,
        *,
        name: str,
        issuer: str = "",
        expires_on: str = "",
        company_id: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("license name required")
        lid = _id("cp_lic")
        return self.store.cp_licenses.save(
            lid,
            {
                "license_id": lid,
                "name": name,
                "issuer": issuer,
                "expires_on": expires_on,
                "company_id": company_id,
                "status": "active",
                "at": _now(),
            },
        )

    def register_permit(self, *, name: str, issuer: str = "", expires_on: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("permit name required")
        pid = _id("cp_prm")
        return self.store.cp_permits.save(
            pid,
            {
                "permit_id": pid,
                "name": name,
                "issuer": issuer,
                "expires_on": expires_on,
                "status": "active",
                "at": _now(),
            },
        )

    def register_certificate(
        self, *, name: str, issuer: str = "", expires_on: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("certificate name required")
        cid = _id("cp_cert")
        return self.store.cp_certificates.save(
            cid,
            {
                "certificate_id": cid,
                "name": name,
                "issuer": issuer,
                "expires_on": expires_on,
                "status": "active",
                "at": _now(),
            },
        )

    def monitor_expiration(self, *, license_id: str = "", permit_id: str = "", certificate_id: str = "") -> dict[str, Any]:
        target = None
        kind = ""
        tid = ""
        if license_id:
            target = self.store.cp_licenses.get(license_id)
            kind, tid = "license", license_id
        elif permit_id:
            target = self.store.cp_permits.get(permit_id)
            kind, tid = "permit", permit_id
        elif certificate_id:
            target = self.store.cp_certificates.get(certificate_id)
            kind, tid = "certificate", certificate_id
        else:
            raise ValidationError("license_id, permit_id, or certificate_id required")
        if target is None:
            raise NotFoundError(kind, tid)
        mid = _id("cp_exp")
        return self.store.cp_expirations.save(
            mid,
            {
                "monitor_id": mid,
                "kind": kind,
                "target_id": tid,
                "expires_on": target.get("expires_on"),
                "status": "watching",
                "at": _now(),
            },
        )

    def start_renewal(self, *, target_id: str, kind: str = "license", due_on: str = "") -> dict[str, Any]:
        if not target_id:
            raise ValidationError("target_id required")
        rid = _id("cp_ren")
        return self.store.cp_renewals.save(
            rid,
            {
                "renewal_id": rid,
                "kind": kind,
                "target_id": target_id,
                "due_on": due_on,
                "status": "in_progress",
                "at": _now(),
            },
        )

    def notify_renewal(self, *, renewal_id: str, channel: str = "email") -> dict[str, Any]:
        renewal = self.store.cp_renewals.get(renewal_id)
        if renewal is None:
            raise NotFoundError("renewal", renewal_id)
        nid = _id("cp_ntf")
        return self.store.cp_renewal_notifications.save(
            nid,
            {
                "notification_id": nid,
                "renewal_id": renewal_id,
                "channel": channel,
                "status": "sent",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "licenses": self.store.cp_licenses.count(),
            "permits": self.store.cp_permits.count(),
            "certificates": self.store.cp_certificates.count(),
            "expirations": self.store.cp_expirations.count(),
            "renewals": self.store.cp_renewals.count(),
            "notifications": self.store.cp_renewal_notifications.count(),
        }

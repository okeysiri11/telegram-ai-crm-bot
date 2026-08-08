"""Epic 46.0 — Enterprise Certification report."""

from __future__ import annotations

from typing import Any

from platform_product.audit import product_audit
from platform_product.release_checklist import release_checklist

CERT_AREAS = (
    "Backend",
    "Frontend",
    "Telegram",
    "Voice",
    "AI Studio",
    "Memory",
    "Workflow",
    "Hercules",
    "Security",
    "Performance",
    "Localization",
    "Documentation",
    "Testing",
    "Production Readiness",
)


class EnterpriseCertification:
    VERSION = "46.0.0"

    def area_status(self, area: str, *, audit_ok: bool) -> dict[str, Any]:
        # Product polish epic: READY when audit + checklist pass
        status = "READY" if audit_ok else "WARNING"
        return {"area": area, "status": status}

    def run(self) -> dict[str, Any]:
        audit = product_audit.full_product_audit()
        checklist = release_checklist.run(audit_ok=audit["ok"])
        audit_ok = audit["ok"] and checklist["ok"]
        areas = [self.area_status(a, audit_ok=audit_ok) for a in CERT_AREAS]
        blocked = [a for a in areas if a["status"] == "BLOCKED"]
        warnings = [a for a in areas if a["status"] == "WARNING"]
        overall = "READY" if audit_ok and not blocked else ("WARNING" if warnings else "BLOCKED")
        return {
            "version": self.VERSION,
            "overall": overall,
            "enterprise_production_readiness": overall,
            "areas": areas,
            "audit": audit,
            "release_checklist": checklist,
            "ready": overall == "READY",
        }


enterprise_certification = EnterpriseCertification()

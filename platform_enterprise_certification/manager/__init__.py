"""Certification Manager — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import CERT_FIELDS


class CertificationManager:
    def create(
        self,
        *,
        certification_id: str,
        platform_version: str,
        build_number: str,
        release_candidate: str,
        certification_date: str,
        approved_by: str = "pending",
        status: str = "in_progress",
        result: str = "pending",
    ) -> dict[str, Any]:
        if not certification_id or not platform_version:
            raise ValueError("certification_id and platform_version are required")
        return {
            "certification_id": certification_id,
            "platform_version": platform_version,
            "build_number": build_number,
            "release_candidate": release_candidate,
            "certification_date": certification_date,
            "result": result,
            "approved_by": approved_by,
            "status": status,
            "fields": list(CERT_FIELDS),
        }

    def finalize(self, cert: dict[str, Any], *, passed: bool, approved_by: str = "owner") -> dict[str, Any]:
        out = dict(cert)
        out["result"] = "passed" if passed else "failed"
        out["status"] = "certified" if passed else "rejected"
        out["approved_by"] = approved_by if passed else "n/a"
        return out

    def plan(self, *, release: str) -> dict[str, Any]:
        if not release:
            raise ValueError("release is required")
        return {
            "release": release,
            "gate": "enterprise_certification",
            "block_on_critical": True,
            "suites": [
                "quality_gates",
                "architecture",
                "documentation",
                "readiness",
                "release_builder",
                "version_manager",
            ],
        }

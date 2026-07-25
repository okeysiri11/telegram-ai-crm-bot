"""Certification Suite — Sprint 25.7 / v8.7.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_certification.facade import CertificationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CertificationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = CertificationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = CertificationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ecf_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ecf_bootstraps.save(bid, record)
        cid = full["certification"]["certification_id"]
        self.store.ecf_certifications.save(cid, {**full["certification"], "created_at": _now()})
        for key, attr, prefix in (
            ("quality", "ecf_quality", "ecf_qg"),
            ("architecture", "ecf_architecture", "ecf_arch"),
            ("documentation", "ecf_documentation", "ecf_doc"),
            ("readiness", "ecf_readiness", "ecf_rdy"),
            ("package", "ecf_packages", "ecf_pkg"),
            ("versions", "ecf_versions", "ecf_ver"),
            ("release", "ecf_releases", "ecf_rel"),
            ("reports", "ecf_reports", "ecf_rep"),
            ("dashboard", "ecf_dashboards", "ecf_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.ecf_bootstraps.save(bid, record)
        return record

    def run_gate(
        self,
        *,
        release: str | None = None,
        failed_gates: list[str] | None = None,
        missing_architecture: list[str] | None = None,
        missing_docs: list[str] | None = None,
        readiness_scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        release = release or DEFAULT_CONFIG.application_version
        plan = self.library.manager.plan(release=release)
        try:
            cert = self.library.manager.create(
                certification_id=_id("cert"),
                platform_version=release,
                build_number=release.replace(".", ""),
                release_candidate=f"{release}-rc1",
                certification_date=_now()[:10],
            )
            quality = self.library.quality.evaluate(failed=failed_gates)
            architecture = self.library.architecture.validate(missing=missing_architecture)
            documentation = self.library.documentation.validate(missing=missing_docs)
            readiness = self.library.readiness.analyze(scores=readiness_scores)
            package = self.library.release_builder.build(
                version=release,
                build_number=release.replace(".", ""),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        versions = self.library.versions.snapshot(
            current=release,
            previous="8.6.0",
            release_candidate=f"{release}-rc1",
            production_version=release if quality["passed"] else None,
            build_history=[{"build": release.replace(".", ""), "version": release}],
            release_history=[{"version": "8.6.0", "status": "previous"}],
        )
        release_result = self.library.release_validator.validate(
            quality_passed=quality["passed"],
            architecture_passed=architecture["passed"],
            documentation_passed=documentation["passed"],
            readiness_passed=readiness["passed"],
            package_ready=package["package_ready"],
        )
        cert = self.library.manager.finalize(
            cert,
            passed=release_result["passed"],
            approved_by="owner" if release_result["passed"] else "n/a",
        )
        release_blocked = not release_result["passed"]
        reports = self.library.reports.generate(
            run_id=_id("ecf_run"),
            summary={
                "enterprise_certified": release_result["enterprise_certified"],
                "release_blocked": release_blocked,
                "overall_readiness": readiness["overall_readiness_percent"],
            },
        )
        dash = self.library.dashboard.render(
            overall_readiness=readiness["overall_readiness_percent"],
            quality_gates=quality,
            test_results={"all_passed": quality["passed"]},
            security_status="verified" if quality["passed"] else "blocked",
            performance_status="verified" if quality["passed"] else "blocked",
            deployment_status="ready" if release_result["passed"] else "blocked",
            documentation=documentation,
            release_candidate=f"{release}-rc1",
            final_certification=cert,
            enterprise_ready=release_result["enterprise_certified"],
            recommendations=(
                ["ENTERPRISE READY", "phase3_web_platform"]
                if release_result["passed"]
                else ["fix_failed_gates"]
            ),
        )
        rid = _id("ecf_run")
        record = {
            "run_id": rid,
            "plan": plan,
            "certification": cert,
            "quality": quality,
            "architecture": architecture,
            "documentation": documentation,
            "readiness": readiness,
            "package": package,
            "versions": versions,
            "release": release_result,
            "reports": reports,
            "dashboard": dash,
            "release_blocked": release_blocked,
            "enterprise_certified": release_result["enterprise_certified"],
            "production_ready": release_result["production_ready"],
            "release_approved": release_result["release_approved"],
            "ready_for_enterprise_web_platform": release_result["ready_for_enterprise_web_platform"],
            "enterprise_ready": release_result["enterprise_certified"],
            "status": "ENTERPRISE READY" if release_result["passed"] else "NOT READY",
            "created_at": _now(),
        }
        self.store.ecf_runs.save(rid, record)
        self.store.ecf_certifications.save(cert["certification_id"], {**cert, "created_at": _now()})
        did = _id("ecf_dash")
        self.store.ecf_dashboards.save(did, {"dashboard_id": did, **dash, "created_at": _now()})
        rep_id = _id("ecf_rep")
        self.store.ecf_reports.save(rep_id, {"report_id": rep_id, **reports, "created_at": _now()})
        return record

    def dashboard(self) -> dict[str, Any]:
        runs = self.store.ecf_runs.list_all()
        if runs:
            return runs[-1].get("dashboard") or self.run_gate()["dashboard"]
        return self.run_gate()["dashboard"]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ecf_bootstraps.list_all()),
            "runs": len(self.store.ecf_runs.list_all()),
            "certifications": len(self.store.ecf_certifications.list_all()),
            "block_on_critical": True,
        }


certification = CertificationSuite()

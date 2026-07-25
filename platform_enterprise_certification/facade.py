"""Certification library facade — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.architecture import ArchitectureValidator
from platform_enterprise_certification.dashboard import CertificationDashboard
from platform_enterprise_certification.documentation import DocumentationValidator
from platform_enterprise_certification.integrations import CertificationIntegrations
from platform_enterprise_certification.manager import CertificationManager
from platform_enterprise_certification.models import PRINCIPLES
from platform_enterprise_certification.quality import QualityGate
from platform_enterprise_certification.readiness import ReadinessAnalyzer
from platform_enterprise_certification.release_builder import ReleaseBuilder
from platform_enterprise_certification.release_validator import ReleaseValidator
from platform_enterprise_certification.reports import ReleaseReports
from platform_enterprise_certification.versions import VersionManager


class CertificationLibrary:
    def __init__(self) -> None:
        self.manager = CertificationManager()
        self.release_validator = ReleaseValidator()
        self.readiness = ReadinessAnalyzer()
        self.quality = QualityGate()
        self.architecture = ArchitectureValidator()
        self.documentation = DocumentationValidator()
        self.release_builder = ReleaseBuilder()
        self.versions = VersionManager()
        self.dashboard = CertificationDashboard()
        self.reports = ReleaseReports()
        self.integrations = CertificationIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        plan = self.manager.plan(release="8.7.0")
        cert = self.manager.create(
            certification_id="cert_8_7_0",
            platform_version="8.7.0",
            build_number="8700",
            release_candidate="8.7.0-rc1",
            certification_date="2026-07-25",
        )
        quality = self.quality.evaluate()
        architecture = self.architecture.validate()
        documentation = self.documentation.validate()
        readiness = self.readiness.analyze()
        package = self.release_builder.build(version="8.7.0", build_number="8700")
        versions = self.versions.snapshot(
            current="8.7.0",
            previous="8.6.0",
            release_candidate="8.7.0-rc1",
            production_version=None,
            build_history=[{"build": "8700", "version": "8.7.0"}],
            release_history=[{"version": "8.6.0", "status": "previous"}],
        )
        release = self.release_validator.validate(
            quality_passed=quality["passed"],
            architecture_passed=architecture["passed"],
            documentation_passed=documentation["passed"],
            readiness_passed=readiness["passed"],
            package_ready=package["package_ready"],
        )
        cert = self.manager.finalize(cert, passed=release["passed"], approved_by="owner")
        reports = self.reports.generate(
            run_id="ecf_boot",
            summary={
                "enterprise_certified": release["enterprise_certified"],
                "overall_readiness": readiness["overall_readiness_percent"],
            },
        )
        dash = self.dashboard.render(
            overall_readiness=readiness["overall_readiness_percent"],
            quality_gates=quality,
            test_results={"all_passed": quality["passed"]},
            security_status="verified" if quality["passed"] else "blocked",
            performance_status="verified" if quality["passed"] else "blocked",
            deployment_status="ready" if release["passed"] else "blocked",
            documentation=documentation,
            release_candidate="8.7.0-rc1",
            final_certification=cert,
            enterprise_ready=release["enterprise_certified"],
            recommendations=["enterprise_ready"] if release["passed"] else ["fix_failed_gates"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "certification_ready": True,
            "quality_gates_ready": True,
            "release_builder_ready": True,
            "enterprise_certified": release["enterprise_certified"],
            "production_ready": release["production_ready"],
            "release_approved": release["release_approved"],
            "ready_for_enterprise_web_platform": release["ready_for_enterprise_web_platform"],
            "enterprise_ready": release["enterprise_certified"],
            "ci_cd_required": True,
            "block_on_critical": True,
            "duplicates_core_logic": False,
            "duplicates_erl_logic": False,
            "phase3_ready": True,
            "next_phase": "enterprise_web_platform",
            "next_version": "9.0.4",
            "status": "ENTERPRISE READY" if release["passed"] else "NOT READY",
            "integrations": links,
            "full": {
                "plan": plan,
                "certification": cert,
                "quality": quality,
                "architecture": architecture,
                "documentation": documentation,
                "readiness": readiness,
                "package": package,
                "versions": versions,
                "release": release,
                "reports": reports,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "manager",
                "release_validator",
                "readiness",
                "quality",
                "architecture",
                "documentation",
                "release_builder",
                "versions",
                "dashboard",
                "reports",
            ],
            "principles": self.principles(),
            "block_on_critical": True,
        }


certification_library = CertificationLibrary()

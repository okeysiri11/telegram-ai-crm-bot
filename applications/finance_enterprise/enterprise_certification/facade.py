"""Finance Enterprise Certification Suite facade — Sprint 18.8."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.enterprise_certification.engines import (
    ArchitectureValidator,
    DocumentationCertifier,
    ExecutiveReadiness,
    FinancialIntegrityCertifier,
    IntegrationCertifier,
    PerformanceCertifier,
    QualityCertifier,
    ReleasePack,
    SecurityCertifier,
)
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class FinanceEnterpriseCertificationSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.architecture = ArchitectureValidator()
        self.integration = IntegrationCertifier()
        self.performance = PerformanceCertifier()
        self.security = SecurityCertifier()
        self.financial_integrity = FinancialIntegrityCertifier()
        self.documentation = DocumentationCertifier()
        self.quality = QualityCertifier()
        self.release = ReleasePack()
        self.executive = ExecutiveReadiness()

    def run_all(self) -> dict[str, Any]:
        arch = self.architecture.validate()
        integ = self.integration.certify()
        perf = self.performance.benchmark()
        sec = self.security.audit()
        fin = self.financial_integrity.certify()
        docs = self.documentation.certify()
        qa = self.quality.certify()
        scorecard = self.executive.scorecard(
            architecture=arch,
            integration=integ,
            performance=perf,
            security=sec,
            financial_integrity=fin,
            documentation=docs,
            quality=qa,
        )
        pack = self.release.package()
        result = {
            "bootstrap": True,
            "certification": True,
            "version": DEFAULT_CONFIG.application_version,
            "architecture": arch,
            "integration": integ,
            "performance": perf,
            "security": sec,
            "financial_integrity": fin,
            "documentation": docs,
            "quality": qa,
            "module_registry": pack["module_registry"],
            "version_manifest": pack["version_manifest"],
            "deployment_manifest": pack["deployment_manifest"],
            "executive": scorecard,
            "architecture_certified": arch["certified"],
            "integration_certified": integ["certified"],
            "security_certified": sec["certified"],
            "performance_certified": perf["certified"],
            "financial_integrity_certified": fin["certified"],
            "documentation_certified": docs["certified"],
            "quality_certified": qa["certified"],
            "finance_enterprise_ready": scorecard["finance_enterprise_ready"],
            "production_ready": scorecard["production_readiness"],
            "enterprise_release_ready": scorecard["enterprise_release_ready"],
            "bidex_finance_enterprise_suite_released": scorecard["production_readiness"],
            "all_enterprise_tests_passed": qa["certified"] and scorecard["production_readiness"],
        }
        self.store.fec_runs.save(f"run_{DEFAULT_CONFIG.application_version}", result)
        return result

    def bootstrap(self) -> dict[str, Any]:
        return self.run_all()

    def dashboard(self, *, dashboard_type: str = "enterprise_health") -> dict[str, Any]:
        allowed = {
            "enterprise_health",
            "certification",
            "performance",
            "security",
            "release",
        }
        if dashboard_type not in allowed:
            from applications.finance_enterprise.shared.exceptions import ValidationError

            raise ValidationError(f"dashboard_type must be one of {sorted(allowed)}")
        result = self.run_all()
        payload = {
            "dashboard_type": dashboard_type,
            "version": result["version"],
            "metrics": {
                "readiness_score": result["executive"]["enterprise_readiness_score"],
                "status": result["executive"]["status"],
                "certified": {
                    "architecture": result["architecture_certified"],
                    "integration": result["integration_certified"],
                    "performance": result["performance_certified"],
                    "security": result["security_certified"],
                    "financial_integrity": result["financial_integrity_certified"],
                    "documentation": result["documentation_certified"],
                    "quality": result["quality_certified"],
                },
            },
            "suite": dashboard_type,
        }
        self.store.fec_dashboards.save(f"dash_{dashboard_type}", payload)
        return payload

    def status(self) -> dict[str, Any]:
        result = self.run_all()
        return {
            "version": result["version"],
            "architecture_certified": result["architecture_certified"],
            "integration_certified": result["integration_certified"],
            "security_certified": result["security_certified"],
            "performance_certified": result["performance_certified"],
            "financial_integrity_certified": result["financial_integrity_certified"],
            "documentation_certified": result["documentation_certified"],
            "quality_certified": result["quality_certified"],
            "finance_enterprise_ready": result["finance_enterprise_ready"],
            "production_ready": result["production_ready"],
            "enterprise_release_ready": result["enterprise_release_ready"],
            "bidex_finance_enterprise_suite_released": result[
                "bidex_finance_enterprise_suite_released"
            ],
            "readiness_score": result["executive"]["enterprise_readiness_score"],
        }


finance_enterprise_certification = FinanceEnterpriseCertificationSuite()

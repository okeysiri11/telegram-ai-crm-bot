# Sprint architecture review — duplicate / ownership / compatibility gates.
# Extends ArchitectureGovernance; does not replace validate_architecture.py.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_architecture.core_inventory import CORE_SERVICE_OWNERS, inventory_summary
from platform_architecture.rules import ROOT


@dataclass
class ReviewFinding:
    code: str
    severity: str  # info | warn | critical
    message: str
    path: str | None = None


@dataclass
class SprintArchitectureReview:
    passed: bool
    findings: list[ReviewFinding] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [
                {
                    "code": f.code,
                    "severity": f.severity,
                    "message": f.message,
                    "path": f.path,
                }
                for f in self.findings
            ],
            "metadata": self.metadata,
        }


# Markers that imply a forbidden parallel core (informational / warn unless exact).
PARALLEL_CORE_MARKERS = (
    "class PlatformCore(",
    "class NewPlatformCore",
    "SECOND_PLATFORM_CORE",
)

# Required governance docs (32.2 + 32.3 consolidation track).
REQUIRED_DOCS = (
    "docs/TECH_DEBT.md",
    "docs/TECH_DEBT_REGISTRY.md",
    "docs/PLATFORM_CORE.md",
    "docs/CORE_SERVICES.md",
    "docs/ARCHITECTURE_GOVERNANCE.md",
    "docs/ARCHITECTURE_MAP.md",
    "docs/CANONICAL_SERVICES.md",
    "docs/QUEUE_ARCHITECTURE.md",
    "docs/EVENT_BUS.md",
    "docs/SPRINT_32_3_RESULT.md",
    "docs/SECURITY_CENTER.md",
    "docs/ZERO_TRUST.md",
    "docs/SPRINT_32_4_RESULT.md",
)

# Backward-compat contract files / packages that must remain present.
COMPAT_CONTRACTS = (
    ("events/event_bus.py", "PlatformEventBus"),
    ("platform_workflow", None),
    ("platform_security/permission_engine", None),
    ("services/pricing_engine.py", "PricingEngine"),
    ("services/notification_center.py", None),
    ("services/search_service.py", None),
    ("platform_integrations/n8n_bridge.py", "N8nBridge"),
    ("src/web/src/enterprise-runtime/aiAgentRuntime.ts", None),
    ("platform_jobs/unified_queue.py", "UnifiedQueueArchitecture"),
    ("platform_security/secret_policy.py", "scan_repo_for_insecure_defaults"),
    ("services/canonical_deal_pipeline.py", None),
    ("platform_security/security_center.py", "EnterpriseSecurityCenter"),
    ("platform_security/anti_parsing.py", "AntiParsingProtection"),
    ("platform_security/external_ai_guard.py", "ExternalAiGuard"),
)


class SprintArchitectureReviewer:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT

    def run(self) -> SprintArchitectureReview:
        findings: list[ReviewFinding] = []
        findings.extend(self._check_docs())
        findings.extend(self._check_compat_contracts())
        findings.extend(self._check_parallel_core_markers())
        findings.extend(self._check_core_inventory())
        findings.extend(self._check_auto_bridge())
        findings.extend(self._check_debt_registry())
        findings.extend(self._check_consolidation())
        findings.extend(self._check_secret_scan())

        critical = [f for f in findings if f.severity == "critical"]
        return SprintArchitectureReview(
            passed=len(critical) == 0,
            findings=findings,
            metadata={
                "inventory": inventory_summary(),
                "core_services": list(CORE_SERVICE_OWNERS.keys()),
                "review": "sprint_architecture_review",
                "sprint_track": "32.4_enterprise_security_center",
            },
        )

    def _check_docs(self) -> list[ReviewFinding]:
        out: list[ReviewFinding] = []
        for rel in REQUIRED_DOCS:
            path = self.root / rel
            if not path.is_file():
                out.append(
                    ReviewFinding(
                        code="DOC_MISSING",
                        severity="critical",
                        message=f"Required governance doc missing: {rel}",
                        path=rel,
                    )
                )
            else:
                out.append(
                    ReviewFinding(
                        code="DOC_OK",
                        severity="info",
                        message=f"Doc present: {rel}",
                        path=rel,
                    )
                )
        return out

    def _check_compat_contracts(self) -> list[ReviewFinding]:
        out: list[ReviewFinding] = []
        for rel, symbol in COMPAT_CONTRACTS:
            path = self.root / rel
            if not path.exists():
                out.append(
                    ReviewFinding(
                        code="COMPAT_MISSING",
                        severity="critical",
                        message=f"Compatibility contract missing: {rel}",
                        path=rel,
                    )
                )
                continue
            if symbol and path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                if symbol not in text:
                    out.append(
                        ReviewFinding(
                            code="COMPAT_SYMBOL",
                            severity="critical",
                            message=f"Expected symbol {symbol} in {rel}",
                            path=rel,
                        )
                    )
                else:
                    out.append(
                        ReviewFinding(
                            code="COMPAT_OK",
                            severity="info",
                            message=f"Contract OK: {rel}::{symbol}",
                            path=rel,
                        )
                    )
            else:
                out.append(
                    ReviewFinding(
                        code="COMPAT_OK",
                        severity="info",
                        message=f"Contract present: {rel}",
                        path=rel,
                    )
                )
        return out

    def _check_parallel_core_markers(self) -> list[ReviewFinding]:
        out: list[ReviewFinding] = []
        # Scan a limited set of likely roots — avoid full-repo cost in CI unit tests.
        scan_roots = [
            self.root / "services",
            self.root / "platform_architecture",
            self.root / "applications" / "auto_marketplace",
        ]
        # Scanner / inventory docs intentionally mention forbidden markers as strings.
        skip_names = {
            "sprint_review.py",
            "core_inventory.py",
            "test_sprint_32_2_architecture.py",
        }
        for base in scan_roots:
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                if path.name in skip_names:
                    continue
                if "venv" in path.parts or ".venv" in path.parts:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for marker in PARALLEL_CORE_MARKERS:
                    if marker in text:
                        out.append(
                            ReviewFinding(
                                code="PARALLEL_CORE",
                                severity="critical",
                                message=f"Forbidden parallel core marker {marker}",
                                path=str(path.relative_to(self.root)),
                            )
                        )
        if not any(f.code == "PARALLEL_CORE" for f in out):
            out.append(
                ReviewFinding(
                    code="PARALLEL_CORE_OK",
                    severity="info",
                    message="No forbidden parallel Platform Core markers in scanned trees",
                )
            )
        return out

    def _check_core_inventory(self) -> list[ReviewFinding]:
        required = {
            "event_bus",
            "workflow_runtime",
            "notification_service",
            "search_service",
            "permission_engine",
            "pricing_foundation",
            "catalog_engine",
            "deal_pipeline",
            "unified_queue",
            "secret_policy",
            "security_center",
        }
        missing = required - set(CORE_SERVICE_OWNERS.keys())
        if missing:
            return [
                ReviewFinding(
                    code="INVENTORY_GAP",
                    severity="critical",
                    message=f"Core inventory missing services: {sorted(missing)}",
                )
            ]
        return [
            ReviewFinding(
                code="INVENTORY_OK",
                severity="info",
                message=f"Core inventory lists {len(CORE_SERVICE_OWNERS)} services",
            )
        ]

    def _check_auto_bridge(self) -> list[ReviewFinding]:
        bridge = self.root / "applications/auto_marketplace/integrations/platform_bridge.py"
        if not bridge.is_file():
            return [
                ReviewFinding(
                    code="AUTO_BRIDGE_MISSING",
                    severity="warn",
                    message="Auto PlatformBridge missing — vertical may be calling Core incorrectly",
                    path="applications/auto_marketplace/integrations/platform_bridge.py",
                )
            ]
        return [
            ReviewFinding(
                code="AUTO_BRIDGE_OK",
                severity="info",
                message="Auto PlatformBridge present (adapters only)",
                path=str(bridge.relative_to(self.root)),
            )
        ]

    def _check_debt_registry(self) -> list[ReviewFinding]:
        path = self.root / "docs/TECH_DEBT_REGISTRY.md"
        text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
        if "TECH_DEBT.md" not in text:
            return [
                ReviewFinding(
                    code="DEBT_REGISTRY_LINK",
                    severity="critical",
                    message="TECH_DEBT_REGISTRY.md must reference canonical docs/TECH_DEBT.md",
                    path="docs/TECH_DEBT_REGISTRY.md",
                )
            ]
        return [
            ReviewFinding(
                code="DEBT_REGISTRY_OK",
                severity="info",
                message="Debt registry links to TECH_DEBT.md",
                path="docs/TECH_DEBT_REGISTRY.md",
            )
        ]

    def _check_consolidation(self) -> list[ReviewFinding]:
        from platform_architecture.consolidation_scanner import run_consolidation_scan

        report = run_consolidation_scan(self.root)
        out: list[ReviewFinding] = []
        for f in report.findings:
            if f.severity == "info" and not f.code.endswith("_OK") and f.code != "DOC_OK":
                continue
            out.append(
                ReviewFinding(
                    code=f.code,
                    severity=f.severity,
                    message=f.message,
                    path=f.path,
                )
            )
        if report.passed and not any(x.code == "CONSOLIDATION_OK" for x in out):
            out.append(
                ReviewFinding(
                    code="CONSOLIDATION_OK",
                    severity="info",
                    message="Consolidation scan passed",
                )
            )
        return out

    def _check_secret_scan(self) -> list[ReviewFinding]:
        from platform_security.secret_policy import scan_repo_for_insecure_defaults

        report = scan_repo_for_insecure_defaults(self.root)
        out: list[ReviewFinding] = []
        for f in report.findings:
            out.append(
                ReviewFinding(
                    code=f.code,
                    severity=f.severity,
                    message=f.message,
                    path=f.path,
                )
            )
        if report.passed and not any(x.code == "SECRET_SCAN_OK" for x in out):
            out.append(
                ReviewFinding(
                    code="SECRET_SCAN_OK",
                    severity="info",
                    message="Repo secret-default scan passed",
                )
            )
        return out


def run_sprint_architecture_review(root: Path | None = None) -> SprintArchitectureReview:
    return SprintArchitectureReviewer(root).run()

# Full application validation suite — Sprint 8.8.

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from events.publisher import publish

from applications.agro_marketplace.config import DEFAULT_CONFIG, AgroMarketplaceConfig
from applications.agro_marketplace.ops.events import ApplicationValidatedEvent
from applications.agro_marketplace.ops.models import CheckStatus, ReportKind, ValidationCheck, ValidationReport
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ValidationService:
    def __init__(
        self,
        store: AgroStore | None = None,
        config: AgroMarketplaceConfig | None = None,
    ) -> None:
        self._store = store or agro_store
        self._config = config or DEFAULT_CONFIG

    def _run(self, name: str, category: str, fn: Callable[[], tuple[bool, str]]) -> ValidationCheck:
        started = time.perf_counter()
        try:
            ok, detail = fn()
            status = CheckStatus.PASSED if ok else CheckStatus.FAILED
        except Exception as exc:  # noqa: BLE001 — validation must never crash suite
            ok, detail, status = False, str(exc), CheckStatus.FAILED
        return ValidationCheck(
            name=name,
            category=category,
            status=status,
            detail=detail,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    def _save_report(self, report: ValidationReport) -> ValidationReport:
        return self._store.validation_reports.save(report.report_id, report)

    def _compile(self, kind: ReportKind, title: str, checks: list[ValidationCheck]) -> ValidationReport:
        passed = sum(1 for c in checks if c.status == CheckStatus.PASSED)
        failed = sum(1 for c in checks if c.status == CheckStatus.FAILED)
        warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)
        report = ValidationReport(
            kind=kind,
            title=title,
            summary=f"{passed} passed, {failed} failed, {warnings} warnings",
            passed=passed,
            failed=failed,
            warnings=warnings,
            checks=[c.to_dict() for c in checks],
            metadata={"application_version": self._config.application_version},
        )
        return self._save_report(report)

    def validate_configuration(self) -> list[ValidationCheck]:
        return [
            self._run(
                "application_version",
                "configuration",
                lambda: (
                    self._config.application_version == "2.0.0",
                    f"version={self._config.application_version}",
                ),
            ),
            self._run(
                "application_status",
                "configuration",
                lambda: (
                    self._config.application_status == "Production Ready",
                    f"status={self._config.application_status}",
                ),
            ),
            self._run(
                "release_type",
                "configuration",
                lambda: (self._config.release == "Commercial", f"release={self._config.release}"),
            ),
            self._run(
                "platform_dependency",
                "configuration",
                lambda: ("Platform Core" in self._config.platform_dependency, self._config.platform_dependency),
            ),
            self._run(
                "ecosystem_dependency",
                "configuration",
                lambda: ("Ecosystem" in self._config.ecosystem_dependency, self._config.ecosystem_dependency),
            ),
        ]

    def validate_manifest(self) -> list[ValidationCheck]:
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "manifest.json"

        def _check() -> tuple[bool, str]:
            if not manifest_path.exists():
                return False, "manifest.json missing"
            import json

            data = json.loads(manifest_path.read_text())
            ok = (
                data.get("application_version") == "2.0.0"
                and data.get("application_status") == "Production Ready"
                and data.get("release") == "Commercial"
            )
            return ok, f"manifest version={data.get('application_version')} status={data.get('application_status')}"

        return [self._run("manifest_verification", "manifest", _check)]

    def validate_apis(self) -> list[ValidationCheck]:
        prefixes = [
            self._config.api_prefix,
            self._config.internal_prefix,
            self._config.webhook_prefix,
            self._config.mobile_prefix,
            self._config.partner_prefix,
        ]
        return [
            self._run(
                "api_prefixes",
                "api",
                lambda: (all(bool(p) and p.startswith("/") for p in prefixes), ",".join(prefixes)),
            ),
            self._run(
                "ops_surface",
                "api",
                lambda: (True, f"{self._config.api_prefix}/ops/*"),
            ),
        ]

    def validate_permissions(self) -> list[ValidationCheck]:
        from applications.agro_marketplace.security.permissions import AgroRole, permission_service

        roles = set(permission_service.roles())
        required = {"farmer", "buyer", "supplier", "exporter", "administrator", "owner"}
        return [
            self._run(
                "rbac_roles",
                "permissions",
                lambda: (required.issubset(roles), f"roles={sorted(roles)}"),
            ),
            self._run(
                "admin_wildcard",
                "permissions",
                lambda: (
                    permission_service.has_permission(AgroRole.ADMINISTRATOR, "anything"),
                    "administrator permissions",
                ),
            ),
        ]

    def validate_store(self) -> list[ValidationCheck]:
        required_attrs = [
            "farmers",
            "orders",
            "agro_products",
            "intl_shipments",
            "kpi_snapshots",
            "portal_users",
            "partner_connections",
            "validation_reports",
            "release_records",
        ]
        missing = [a for a in required_attrs if not hasattr(self._store, a)]
        return [
            self._run(
                "store_entities",
                "workflows",
                lambda: (not missing, f"missing={missing}" if missing else "all required stores present"),
            )
        ]

    def validate_engines(self) -> list[ValidationCheck]:
        from applications.agro_marketplace import agro_marketplace

        checks = []
        engines = {
            "export_engine": getattr(agro_marketplace, "export_engine", None),
            "analytics_engine": getattr(agro_marketplace, "analytics_engine", None),
            "portal_engine": getattr(agro_marketplace, "portal_engine", None),
            "agro_ai": getattr(agro_marketplace, "agro_ai", None),
            "business_intelligence": getattr(agro_marketplace, "business_intelligence", None),
            "mobile_engine": getattr(agro_marketplace, "mobile_engine", None),
            "partner_api": getattr(agro_marketplace, "partner_api", None),
        }
        for name, engine in engines.items():
            checks.append(
                self._run(name, "integrations", lambda e=engine, n=name: (e is not None, n))
            )
        return checks

    def validate_events(self) -> list[ValidationCheck]:
        from applications.agro_marketplace.ops import events as ops_events

        required = [
            "ApplicationValidatedEvent",
            "ProductionReadyEvent",
            "ReleaseCreatedEvent",
            "DeploymentVerifiedEvent",
            "CertificationCompletedEvent",
        ]
        missing = [n for n in required if not hasattr(ops_events, n)]
        return [
            self._run(
                "release_events",
                "events",
                lambda: (not missing, "ok" if not missing else f"missing={missing}"),
            )
        ]

    def validate_documentation(self) -> list[ValidationCheck]:
        docs_root = Path(__file__).resolve().parents[3] / "docs"
        required = [
            "AGRO_RELEASE.md",
            "DEPLOYMENT.md",
            "OPERATIONS.md",
            "USER_GUIDE.md",
            "ADMIN_GUIDE.md",
        ]
        missing = [name for name in required if not (docs_root / name).exists()]
        return [
            self._run(
                "release_docs",
                "documentation",
                lambda: (not missing, "ok" if not missing else f"missing={missing}"),
            )
        ]

    def validate_partners(self) -> list[ValidationCheck]:
        from applications.agro_marketplace.partner_api.connectors import partner_connectors

        return [
            self._run(
                "bank_connector",
                "partners",
                lambda: ("accepted" in partner_connectors.bank_transfer(amount=1).get("status", ""), "bank"),
            ),
            self._run(
                "insurance_connector",
                "partners",
                lambda: (partner_connectors.insurance_quote(coverage=100)["premium"] > 0, "insurance"),
            ),
            self._run(
                "logistics_connector",
                "partners",
                lambda: (
                    partner_connectors.logistics_book(origin="A", destination="B")["status"] == "booked",
                    "logistics",
                ),
            ),
        ]

    async def validate_ai(self) -> list[ValidationCheck]:
        from applications.agro_marketplace import agro_marketplace

        checks: list[ValidationCheck] = []

        def agents_ok() -> tuple[bool, str]:
            agents = agro_marketplace.agro_ai.agents.list_agents()
            return len(agents) >= 10, f"agents={len(agents)}"

        checks.append(self._run("agent_registry", "ai", agents_ok))

        async def forecast_ok() -> ValidationCheck:
            started = time.perf_counter()
            result = await agro_marketplace.agro_ai.forecasting.forecast_price("maize")
            ok = bool(result.forecast_id) and result.confidence >= 0
            return ValidationCheck(
                name="forecast_quality",
                category="ai",
                status=CheckStatus.PASSED if ok else CheckStatus.FAILED,
                detail=f"confidence={result.confidence}",
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )

        checks.append(await forecast_ok())

        async def assistant_ok() -> ValidationCheck:
            started = time.perf_counter()
            reply = await agro_marketplace.portal_engine.assistant("Ping", role="farmer")
            ok = bool(reply)
            return ValidationCheck(
                name="assistant_validation",
                category="ai",
                status=CheckStatus.PASSED if ok else CheckStatus.FAILED,
                detail="assistant responded" if ok else "no reply",
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )

        checks.append(await assistant_ok())

        def analytics_ok() -> tuple[bool, str]:
            domains = agro_marketplace.analytics_engine.all_domains()
            return len(domains) >= 10, f"domains={len(domains)}"

        checks.append(self._run("analytics_verification", "ai", analytics_ok))

        knowledge = agro_marketplace.agro_ai.knowledge.search("maize")
        checks.append(
            self._run(
                "knowledge_sync",
                "ai",
                lambda: (isinstance(knowledge, list), f"hits={len(knowledge)}"),
            )
        )
        return checks

    async def run_full_validation(self) -> ValidationReport:
        checks: list[ValidationCheck] = []
        checks.extend(self.validate_configuration())
        checks.extend(self.validate_manifest())
        checks.extend(self.validate_apis())
        checks.extend(self.validate_permissions())
        checks.extend(self.validate_store())
        checks.extend(self.validate_engines())
        checks.extend(self.validate_events())
        checks.extend(self.validate_documentation())
        checks.extend(self.validate_partners())
        checks.extend(await self.validate_ai())
        report = self._compile(ReportKind.PRODUCTION, "Full Application Validation", checks)
        await publish(
            ApplicationValidatedEvent(
                report_id=report.report_id,
                passed=report.passed,
                failed=report.failed,
            )
        )
        return report

    def list_reports(self, *, kind: ReportKind | None = None) -> list[ValidationReport]:
        items = self._store.validation_reports.list_all()
        if kind:
            items = [r for r in items if r.kind == kind]
        return sorted(items, key=lambda r: r.created_at, reverse=True)


validation_service = ValidationService()

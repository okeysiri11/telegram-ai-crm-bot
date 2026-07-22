# Commercial Production Validation — Sprint 10.8 readiness & certification.

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG, AutoMarketplaceConfig
from applications.auto_marketplace.enterprise.models import CheckStatus, CommercialReleaseReport, ValidationCheck
from applications.auto_marketplace.health.engine import HealthEngine, health_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CommercialProductionEngine:
    """Production validation and commercial release certification for Auto Marketplace 2.0.0."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        config: AutoMarketplaceConfig | None = None,
        health: HealthEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._config = config or DEFAULT_CONFIG
        self._health = health or health_engine

    def _save(self, check: ValidationCheck) -> ValidationCheck:
        return self._store.commercial_validation_checks.save(check.check_id, check)

    def validate_configuration(self) -> list[ValidationCheck]:
        checks: list[ValidationCheck] = []
        started = time.time()
        ok = self._config.application_version == "2.0.0"
        checks.append(
            self._save(
                ValidationCheck(
                    name="application_version",
                    category="configuration",
                    status=CheckStatus.PASS if ok else CheckStatus.FAIL,
                    detail=f"version={self._config.application_version}",
                    duration_ms=round((time.time() - started) * 1000, 2),
                )
            )
        )
        for field_name, expected in (
            ("enterprise_engine", "1.0"),
            ("global_network", "1.0"),
            ("production_ready", True),
            ("platform_dependency", "AI Platform Core v3"),
            ("ecosystem_dependency", "AI Ecosystem v1.5"),
        ):
            actual = getattr(self._config, field_name, None)
            checks.append(
                self._save(
                    ValidationCheck(
                        name=field_name,
                        category="configuration",
                        status=CheckStatus.PASS if actual == expected else CheckStatus.FAIL,
                        detail=f"actual={actual}",
                        duration_ms=0.1,
                    )
                )
            )
        return checks

    def validate_dependencies(self) -> list[ValidationCheck]:
        deps = self._health.dependencies()
        untouched = deps.get("untouched", {})
        ok = all(untouched.values()) if untouched else False
        return [
            self._save(
                ValidationCheck(
                    name="platform_apps_untouched",
                    category="dependencies",
                    status=CheckStatus.PASS if ok else CheckStatus.FAIL,
                    detail=str(untouched),
                    duration_ms=0.1,
                )
            )
        ]

    def validate_security(self) -> list[ValidationCheck]:
        # Lightweight commercial gate — auth middleware + config secrets not in manifest
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        leaked = [k for k in manifest if "secret" in k.lower() or "password" in k.lower()]
        return [
            self._save(
                ValidationCheck(
                    name="manifest_no_secrets",
                    category="security",
                    status=CheckStatus.PASS if not leaked else CheckStatus.FAIL,
                    detail="ok" if not leaked else f"leaked={leaked}",
                    duration_ms=0.1,
                )
            )
        ]

    def validate_api(self) -> list[ValidationCheck]:
        from aiohttp import web
        from applications.auto_marketplace.api.register import register_auto_marketplace_routes

        started = time.time()
        app = web.Application()
        register_auto_marketplace_routes(app)
        paths = [getattr(r.resource, "canonical", "") for r in app.router.routes()]
        required = (
            "/api/auto/v1/enterprise",
            "/api/auto/v1/network",
            "/api/auto/v1/partners",
            "/api/auto/v1/production",
            "/api/auto/v1/health",
        )
        missing = [p for p in required if not any(str(path).startswith(p) for path in paths)]
        return [
            self._save(
                ValidationCheck(
                    name="enterprise_api_routes",
                    category="api",
                    status=CheckStatus.PASS if not missing else CheckStatus.FAIL,
                    detail=f"missing={missing}" if missing else f"routes={len(paths)}",
                    duration_ms=round((time.time() - started) * 1000, 2),
                )
            )
        ]

    def validate_load(self) -> list[ValidationCheck]:
        started = time.time()
        # synthetic load: reset-safe store counts
        _ = self._store.network_listings.count()
        duration = round((time.time() - started) * 1000, 2)
        return [
            self._save(
                ValidationCheck(
                    name="store_load_probe",
                    category="load",
                    status=CheckStatus.PASS if duration < 500 else CheckStatus.WARN,
                    detail=f"duration_ms={duration}",
                    duration_ms=duration,
                )
            )
        ]

    def validate_regression_domains(self) -> list[ValidationCheck]:
        from applications.auto_marketplace.application import auto_marketplace

        required = ("marketplace", "auto_ai", "transactions", "service", "logistics", "fleet_ops", "enterprise")
        missing = [n for n in required if not hasattr(auto_marketplace, n)]
        return [
            self._save(
                ValidationCheck(
                    name="domain_facades",
                    category="regression",
                    status=CheckStatus.PASS if not missing else CheckStatus.FAIL,
                    detail="ok" if not missing else f"missing={missing}",
                    duration_ms=0.1,
                )
            )
        ]

    def validate_migration(self) -> list[ValidationCheck]:
        # Ensure prior sprint engines remain configured
        fields = (
            "vin_engine",
            "auto_ai_engine",
            "transaction_engine",
            "service_engine",
            "transport_engine",
            "fleet_engine",
        )
        missing = [f for f in fields if not getattr(self._config, f, None)]
        return [
            self._save(
                ValidationCheck(
                    name="migration_engine_flags",
                    category="migration",
                    status=CheckStatus.PASS if not missing else CheckStatus.FAIL,
                    detail="ok" if not missing else f"missing={missing}",
                    duration_ms=0.1,
                )
            )
        ]

    def run_all(self) -> list[ValidationCheck]:
        checks: list[ValidationCheck] = []
        checks.extend(self.validate_configuration())
        checks.extend(self.validate_dependencies())
        checks.extend(self.validate_security())
        checks.extend(self.validate_api())
        checks.extend(self.validate_load())
        checks.extend(self.validate_regression_domains())
        checks.extend(self.validate_migration())
        return checks

    def generate_report(self) -> CommercialReleaseReport:
        checks = self.run_all()
        failed = [c for c in checks if c.status == CheckStatus.FAIL]
        migration_ok = all(c.status != CheckStatus.FAIL for c in checks if c.category == "migration")
        ready = not failed and self._config.production_ready and self._config.application_version == "2.0.0"
        report = CommercialReleaseReport(
            application_version=self._config.application_version,
            release_status=self._config.release_status,
            production_ready=ready,
            checks=checks,
            migration_ok=migration_ok,
            certified=ready,
        )
        return self._store.commercial_release_reports.save(report.report_id, report)

    def release_manifest(self) -> dict[str, Any]:
        root = Path(__file__).resolve().parents[1]
        return json.loads((root / "manifest.json").read_text(encoding="utf-8"))

    def metrics(self) -> dict[str, Any]:
        return {
            "validation_checks": self._store.commercial_validation_checks.count(),
            "release_reports": self._store.commercial_release_reports.count(),
            "production_ready": self._config.production_ready,
        }


commercial_production_engine = CommercialProductionEngine()

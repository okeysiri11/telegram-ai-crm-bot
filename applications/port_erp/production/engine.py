# Production Engine — readiness, validation, benchmarks, release verification.

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from applications.port_erp.config import DEFAULT_CONFIG, PortERPConfig
from applications.port_erp.deployment.engine import DeploymentEngine, deployment_engine
from applications.port_erp.enterprise.events import ReleaseVerifiedEvent
from applications.port_erp.enterprise.models import CheckStatus, ReleaseReport, ValidationCheck
from applications.port_erp.health.engine import HealthEngine, health_engine
from applications.port_erp.shared.store import PortStore, port_store


class ProductionEngine:
    """Production readiness and commercial release verification for Port ERP 2.0.0."""

    def __init__(
        self,
        store: PortStore | None = None,
        config: PortERPConfig | None = None,
        health: HealthEngine | None = None,
        deployment: DeploymentEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._config = config or DEFAULT_CONFIG
        self._health = health or health_engine
        self._deployment = deployment or deployment_engine
        self._events: list[dict] = []

    def _record(self, check: ValidationCheck) -> ValidationCheck:
        return self._store.validation_checks.save(check.check_id, check)

    def validate_configuration(self) -> list[ValidationCheck]:
        started = time.time()
        checks: list[ValidationCheck] = []
        ok_version = self._config.application_version == "2.0.0"
        checks.append(
            self._record(
                ValidationCheck(
                    name="application_version",
                    category="configuration",
                    status=CheckStatus.PASS if ok_version else CheckStatus.FAIL,
                    detail=f"version={self._config.application_version}",
                    duration_ms=round((time.time() - started) * 1000, 2),
                )
            )
        )
        for field_name, expected in (
            ("enterprise_engine", "1.0"),
            ("global_network", "1.0"),
            ("platform_dependency", "AI Platform Core v3"),
            ("ecosystem_dependency", "AI Ecosystem v1.5"),
        ):
            actual = getattr(self._config, field_name, None)
            checks.append(
                self._record(
                    ValidationCheck(
                        name=field_name,
                        category="configuration",
                        status=CheckStatus.PASS if actual == expected else CheckStatus.FAIL,
                        detail=f"{field_name}={actual}",
                    )
                )
            )
        return checks

    def validate_dependencies(self) -> list[ValidationCheck]:
        probe = self._health.probe()
        checks: list[ValidationCheck] = []
        platform_ok = probe["platform"].get("platform_dependency") == "AI Platform Core v3"
        eco_ok = probe["ecosystem"].get("ecosystem_dependency") == "AI Ecosystem v1.5"
        checks.append(
            self._record(
                ValidationCheck(
                    name="platform_bridge",
                    category="dependency",
                    status=CheckStatus.PASS if platform_ok else CheckStatus.FAIL,
                    detail=str(probe["platform"].get("status")),
                )
            )
        )
        checks.append(
            self._record(
                ValidationCheck(
                    name="ecosystem_bridge",
                    category="dependency",
                    status=CheckStatus.PASS if eco_ok else CheckStatus.FAIL,
                    detail=str(probe["ecosystem"].get("status")),
                )
            )
        )
        manifest_path = Path(__file__).resolve().parents[1] / "manifest.json"
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_ok = data.get("application_version") == "2.0.0"
            detail = f"manifest={data.get('application_version')}"
        except Exception as exc:  # noqa: BLE001
            manifest_ok = False
            detail = str(exc)
        checks.append(
            self._record(
                ValidationCheck(
                    name="manifest",
                    category="dependency",
                    status=CheckStatus.PASS if manifest_ok else CheckStatus.FAIL,
                    detail=detail,
                )
            )
        )
        return checks

    def performance_benchmark(self) -> dict[str, Any]:
        started = time.time()
        key = f"bench-{started}"
        self._store.validation_checks.save(
            key,
            ValidationCheck(
                check_id=key,
                name="benchmark",
                category="performance",
                status=CheckStatus.PASS,
            ),
        )
        _ = self._store.validation_checks.get(key)
        self._store.validation_checks.delete(key)
        elapsed_ms = round((time.time() - started) * 1000, 3)
        check = self._record(
            ValidationCheck(
                name="store_roundtrip",
                category="performance",
                status=CheckStatus.PASS if elapsed_ms < 250 else CheckStatus.WARN,
                detail=f"{elapsed_ms}ms",
                duration_ms=elapsed_ms,
            )
        )
        return {
            "elapsed_ms": elapsed_ms,
            "threshold_ms": 250,
            "passed": check.status == CheckStatus.PASS,
            "check": check.to_dict(),
        }

    def readiness(self) -> dict[str, Any]:
        config_checks = self.validate_configuration()
        dep_checks = self.validate_dependencies()
        bench = self.performance_benchmark()
        all_checks = list(config_checks) + list(dep_checks)
        perf_check = self._store.validation_checks.get(bench["check"]["check_id"])
        if perf_check:
            all_checks.append(perf_check)
        health = self._health.probe()
        blockers = [c.name for c in all_checks if c.status == CheckStatus.FAIL]
        if not health["healthy"]:
            blockers.append("health")
        total = len(all_checks) or 1
        passed = sum(1 for c in all_checks if c.status == CheckStatus.PASS)
        score = round((passed / total) * 100, 2)
        ready = not blockers and self._config.application_version == "2.0.0"
        return {
            "ready": ready,
            "score": score,
            "blockers": blockers,
            "checks": [c.to_dict() for c in all_checks],
            "health": health,
            "benchmark": bench,
            "application_version": self._config.application_version,
        }

    def verify_release(self) -> ReleaseReport:
        ready = self.readiness()
        profile = self._deployment.ensure_production_profile()
        report = ReleaseReport(
            application_version=self._config.application_version,
            ready=bool(ready["ready"]),
            score=float(ready["score"]),
            blockers=list(ready["blockers"]),
            checks=list(ready["checks"]),
        )
        report.checks.append({"deployment_profile": profile.to_dict()})
        self._store.release_reports.save(report.report_id, report)
        event = ReleaseVerifiedEvent(
            report_id=report.report_id,
            ready=report.ready,
            version=report.application_version,
        )
        self._events.append(event.to_dict())
        return report

    def list_reports(self) -> list[ReleaseReport]:
        return self._store.release_reports.list_all()


production_engine = ProductionEngine()

# ProductionReadinessManager — startup, dependency, security, deployment checks.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_validation.models import PlatformHealthReport, ReadinessLevel, ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)


class ProductionReadinessManager:
    """Validates production readiness across startup, deps, config, security, health."""

    def __init__(self) -> None:
        self._checkpoints: list[tuple[str, str, Any]] = []

    def reset(self) -> None:
        self._checkpoints.clear()

    def register_checkpoint(self, check_id: str, component: str, fn: Any) -> None:
        self._checkpoints.append((check_id, component, fn))

    def _run_check(self, check_id: str, component: str, fn: Any) -> ValidationCheck:
        started = time.perf_counter()
        try:
            result = fn()
            ok = bool(result) if not isinstance(result, dict) else result.get("ok", True)
            message = result.get("message", "ok") if isinstance(result, dict) else ("pass" if ok else "fail")
            status = ValidationStatus.PASS if ok else ValidationStatus.FAIL
        except Exception as exc:
            ok = False
            message = str(exc)
            status = ValidationStatus.FAIL
        return ValidationCheck(
            check_id=check_id,
            component=component,
            status=status,
            message=message,
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )

    def validate_startup(self) -> ValidationCheck:
        def check():
            from platform_configuration.configuration_center import configuration_center

            settings = configuration_center.settings
            return {"ok": settings is not None, "message": "Configuration center loaded"}

        return self._run_check("readiness.startup", "startup", check)

    def validate_dependencies(self) -> ValidationCheck:
        def check():
            try:
                from platform_configuration import configuration_manager

                info = configuration_manager.validate_platform()
                return {"ok": info.compatible, "message": f"Dependencies OK ({len(info.components)} components)"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.dependencies", "dependencies", check)

    def validate_configuration(self) -> ValidationCheck:
        def check():
            try:
                from platform_configuration import configuration_manager

                snapshot = configuration_manager.load_configuration(environment="production")
                return {"ok": bool(snapshot.values), "message": f"{len(snapshot.values)} config keys"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.configuration", "configuration", check)

    def validate_security(self) -> ValidationCheck:
        def check():
            try:
                from platform_security import security_manager

                ok = security_manager is not None
                return {"ok": ok, "message": "Security layer initialized"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.security", "security", check)

    def validate_health(self) -> ValidationCheck:
        def check():
            try:
                from platform_observability.health_manager import health_manager

                ok = health_manager is not None
                return {"ok": ok, "message": "Health manager available"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.health", "health", check)

    def validate_deployment(self) -> ValidationCheck:
        def check():
            try:
                from platform_configuration.deployment_manager import deployment_manager

                history = deployment_manager.history()
                return {"ok": True, "message": f"Deployment manager ready ({len(history)} records)"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.deployment", "deployment", check)

    def validate_backup(self) -> ValidationCheck:
        def check():
            try:
                from platform_reliability.checkpoint_manager import checkpoint_manager

                return {"ok": True, "message": f"Checkpoint manager ready"}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.backup", "backup", check)

    def validate_recovery(self) -> ValidationCheck:
        def check():
            try:
                from platform_reliability import reliability_manager

                summary = reliability_manager.metrics_summary()
                return {"ok": True, "message": f"Recovery engine ready", "metadata": summary}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}

        return self._run_check("readiness.recovery", "recovery", check)

    async def validate_all(self) -> ValidationReport:
        report = ValidationReport(title="Production Readiness Report")
        builtins = (
            self.validate_startup,
            self.validate_dependencies,
            self.validate_configuration,
            self.validate_security,
            self.validate_health,
            self.validate_deployment,
            self.validate_backup,
            self.validate_recovery,
        )
        for fn in builtins:
            report.checks.append(fn())
        for check_id, component, checkpoint_fn in self._checkpoints:
            report.checks.append(self._run_check(check_id, component, checkpoint_fn))
        return report.finalize()

    def build_health_report(self, readiness_report: ValidationReport) -> PlatformHealthReport:
        components = {c.component: c.status.value for c in readiness_report.checks}
        failed = any(c.status == ValidationStatus.FAIL for c in readiness_report.checks)
        warned = any(c.status == ValidationStatus.WARN for c in readiness_report.checks)
        if failed:
            level = ReadinessLevel.NOT_READY
            status = ValidationStatus.FAIL
        elif warned:
            level = ReadinessLevel.PARTIAL
            status = ValidationStatus.WARN
        else:
            level = ReadinessLevel.PRODUCTION_READY
            status = ValidationStatus.PASS
        return PlatformHealthReport(
            overall_status=status,
            readiness_level=level,
            components=components,
            metrics={"check_count": len(readiness_report.checks)},
        )


production_readiness_manager = ProductionReadinessManager()

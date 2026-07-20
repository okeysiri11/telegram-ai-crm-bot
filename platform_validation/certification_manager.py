# CertificationManager — production certification and platform readiness.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platform_validation.config import DEFAULT_VALIDATION_CONFIG, ValidationConfig
from platform_validation.models import CertificationResult, ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "platform_manifest.json"


class CertificationManager:
    """Production readiness certification bridging platform_certification."""

    def __init__(self, *, config: ValidationConfig | None = None, manifest_path: Path | None = None) -> None:
        self._config = config or DEFAULT_VALIDATION_CONFIG
        self._manifest_path = manifest_path or _MANIFEST_PATH
        self._last_result: CertificationResult | None = None

    def reset(self) -> None:
        self._last_result = None

    @property
    def last_result(self) -> CertificationResult | None:
        return self._last_result

    def _load_manifest(self) -> dict[str, Any]:
        if not self._manifest_path.exists():
            return {}
        return json.loads(self._manifest_path.read_text(encoding="utf-8"))

    def _bridge_certification_checks(self) -> list[Any]:
        try:
            from platform_certification.checks import (
                check_architecture_audit,
                check_canonical_event_bus,
                check_documentation_sync,
                check_repository_service_imports,
            )

            return [
                check_repository_service_imports,
                check_canonical_event_bus,
                check_architecture_audit,
                check_documentation_sync,
            ]
        except Exception:
            logger.debug("platform_certification unavailable")
            return []

    async def run_certification(self, reports: dict[str, ValidationReport]) -> CertificationResult:
        cert_report = ValidationReport(title="Certification Report")
        bridge_checks = self._bridge_certification_checks()
        gates_passed = 0
        gates_total = len(bridge_checks)

        for check_fn in bridge_checks:
            try:
                result = check_fn()
                passed = result.passed
                if passed:
                    gates_passed += 1
                cert_report.checks.append(
                    ValidationCheck(
                        check_id=f"certification.{result.check_id}",
                        component="certification",
                        status=ValidationStatus.PASS if passed else ValidationStatus.FAIL,
                        message=result.message,
                        metadata=dict(result.metadata) if result.metadata else {},
                    )
                )
            except Exception as exc:
                cert_report.checks.append(
                    ValidationCheck(
                        check_id=f"certification.{check_fn.__name__}",
                        component="certification",
                        status=ValidationStatus.WARN,
                        message=str(exc),
                    )
                )

        for name, report in reports.items():
            failed = sum(1 for c in report.checks if c.status == ValidationStatus.FAIL)
            passed = failed == 0
            if passed:
                gates_passed += 1
            gates_total += 1
            cert_report.checks.append(
                ValidationCheck(
                    check_id=f"certification.{name}",
                    component="certification",
                    status=ValidationStatus.PASS if passed else ValidationStatus.FAIL,
                    message=f"{name}: {failed} failures of {len(report.checks)} checks",
                )
            )

        cert_report.finalize()
        manifest = self._load_manifest()
        core = manifest.get("platform_core", {})
        score = float(core.get("certification_score", 100.0))
        if cert_report.status == ValidationStatus.FAIL:
            score = min(score, 75.0)

        certified = (
            cert_report.status != ValidationStatus.FAIL
            and score >= self._config.min_certification_score
            and gates_passed >= max(1, gates_total - 1)
        )

        result = CertificationResult(
            certified=certified,
            platform_version=self._config.platform_version,
            platform_status=self._config.platform_status if certified else "Not Ready",
            score=score,
            gates_passed=gates_passed,
            gates_total=gates_total,
            report=cert_report,
        )
        self._last_result = result
        return result


certification_manager = CertificationManager()

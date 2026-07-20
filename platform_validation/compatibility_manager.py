# CompatibilityManager — module, API, plugin, config, and version compatibility.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platform_validation.models import ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "platform_manifest.json"


class CompatibilityManager:
    """Validates cross-module and version compatibility."""

    def __init__(self, *, manifest_path: Path | None = None) -> None:
        self._manifest_path = manifest_path or _MANIFEST_PATH

    def reset(self) -> None:
        pass

    def _load_manifest(self) -> dict[str, Any]:
        if not self._manifest_path.exists():
            return {}
        return json.loads(self._manifest_path.read_text(encoding="utf-8"))

    def validate_module_compatibility(self) -> ValidationCheck:
        manifest = self._load_manifest()
        modules = set(manifest.get("modules", []))
        required = {
            "platform_agents",
            "platform_workflow",
            "platform_security",
            "platform_observability",
            "platform_reliability",
            "platform_configuration",
            "platform_validation",
        }
        missing = required - modules
        return ValidationCheck(
            check_id="compatibility.modules",
            component="compatibility",
            status=ValidationStatus.PASS if not missing else ValidationStatus.FAIL,
            message="All required modules present" if not missing else f"Missing: {sorted(missing)}",
            metadata={"missing": sorted(missing)},
        )

    def validate_api_compatibility(self) -> ValidationCheck:
        manifest = self._load_manifest()
        apis = manifest.get("apis", {})
        ok = "management" in apis and "public" in apis
        return ValidationCheck(
            check_id="compatibility.api",
            component="compatibility",
            status=ValidationStatus.PASS if ok else ValidationStatus.FAIL,
            message="API routes defined" if ok else "API routes missing",
            metadata=dict(apis),
        )

    def validate_plugin_compatibility(self) -> ValidationCheck:
        manifest = self._load_manifest()
        sdk = manifest.get("sdk", {})
        ok = bool(sdk.get("plugin_sdk_version"))
        return ValidationCheck(
            check_id="compatibility.plugins",
            component="compatibility",
            status=ValidationStatus.PASS if ok else ValidationStatus.WARN,
            message="Plugin SDK version present" if ok else "Plugin SDK version missing",
            metadata=dict(sdk),
        )

    def validate_configuration_compatibility(self) -> ValidationCheck:
        try:
            from platform_configuration import configuration_manager

            info = configuration_manager.get_version_info()
            ok = info.compatible
            return ValidationCheck(
                check_id="compatibility.configuration",
                component="compatibility",
                status=ValidationStatus.PASS if ok else ValidationStatus.WARN,
                message="Configuration compatible" if ok else f"Issues: {info.issues}",
                metadata=info.to_dict(),
            )
        except Exception as exc:
            return ValidationCheck(
                check_id="compatibility.configuration",
                component="compatibility",
                status=ValidationStatus.WARN,
                message=str(exc),
            )

    def validate_version_compatibility(self) -> ValidationCheck:
        manifest = self._load_manifest()
        core = manifest.get("platform_core", {})
        version = core.get("platform_version", "")
        ok = bool(version) and core.get("architecture_version")
        return ValidationCheck(
            check_id="compatibility.version",
            component="compatibility",
            status=ValidationStatus.PASS if ok else ValidationStatus.FAIL,
            message=f"Platform version {version}" if ok else "Version metadata incomplete",
            metadata={"platform_version": version},
        )

    async def validate_all(self) -> ValidationReport:
        report = ValidationReport(title="Compatibility Report")
        report.checks.extend(
            [
                self.validate_module_compatibility(),
                self.validate_api_compatibility(),
                self.validate_plugin_compatibility(),
                self.validate_configuration_compatibility(),
                self.validate_version_compatibility(),
            ]
        )
        return report.finalize()


compatibility_manager = CompatibilityManager()

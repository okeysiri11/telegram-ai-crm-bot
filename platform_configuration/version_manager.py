# VersionManager — platform and component version tracking.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platform_configuration.layer_exceptions import VersionCompatibilityError
from platform_configuration.models import VersionInfo

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "platform_manifest.json"

_REQUIRED_COMPONENTS = (
    "workflow_engine",
    "tool_framework",
    "security_layer",
    "observability_layer",
    "reliability_layer",
)


class VersionManager:
    """Tracks platform version, component versions, and compatibility."""

    def __init__(self, *, manifest_path: Path | None = None) -> None:
        self._manifest_path = manifest_path or _MANIFEST_PATH
        self._manifest: dict[str, Any] = {}

    def reset(self) -> None:
        self._manifest.clear()

    def load_manifest(self) -> dict[str, Any]:
        if not self._manifest_path.exists():
            logger.warning("manifest_not_found path=%s", self._manifest_path)
            self._manifest = {}
            return self._manifest
        self._manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        return self._manifest

    def get_version_info(self) -> VersionInfo:
        manifest = self._manifest or self.load_manifest()
        core = manifest.get("platform_core", {})
        components = {
            k: str(v)
            for k, v in core.items()
            if k.endswith("_version") or k.endswith("_engine") or k.endswith("_layer") or k.endswith("_framework")
        }
        info = VersionInfo(
            platform_version=str(core.get("platform_version", "2.8.0-alpha")),
            configuration_layer=str(core.get("configuration_layer", "1.0")),
            deployment_framework=str(core.get("deployment_framework", "1.0")),
            feature_flags=str(core.get("feature_flags", "1.0")),
            components=components,
            schema_version=str(core.get("architecture_version", "1.0")),
        )
        info.compatible, info.issues = self._validate_compatibility(core)
        return info

    def _validate_compatibility(self, core: dict[str, Any]) -> tuple[bool, list[str]]:
        issues: list[str] = []
        for component in _REQUIRED_COMPONENTS:
            if component not in core:
                issues.append(f"Missing component version: {component}")
        platform_version = str(core.get("platform_version", ""))
        if not platform_version:
            issues.append("Missing platform_version")
        return len(issues) == 0, issues

    def validate_dependencies(self) -> VersionInfo:
        info = self.get_version_info()
        if not info.compatible:
            raise VersionCompatibilityError(
                "Platform dependency validation failed",
                issues=info.issues,
            )
        return info

    def component_version(self, name: str) -> str | None:
        manifest = self._manifest or self.load_manifest()
        core = manifest.get("platform_core", {})
        return str(core[name]) if name in core else None


version_manager = VersionManager()

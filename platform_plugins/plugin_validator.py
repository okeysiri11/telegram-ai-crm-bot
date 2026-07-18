# Manifest and directory validation.

from __future__ import annotations

import re
from pathlib import Path

from platform_plugins.exceptions import PluginValidationError
from platform_plugins.models import PluginManifest
from platform_plugins.plugin_manifest import PLUGIN_DIRECTORY_LAYOUT

_SEMVER = re.compile(r"^\d+\.\d+\.\d+")
_CONSTRAINT = re.compile(r"^(>=|<=|>|<|==|~)?\s*(\d+\.\d+\.\d+)")


def validate_manifest(manifest: PluginManifest) -> None:
    if not re.match(r"^[a-z][a-z0-9_-]*$", manifest.id):
        raise PluginValidationError(f"Invalid plugin id: {manifest.id}")
    if not _SEMVER.match(manifest.version):
        raise PluginValidationError(f"Invalid semver version: {manifest.version}")
    if not _CONSTRAINT.match(manifest.platform_version.strip()):
        raise PluginValidationError(
            f"Invalid platform_version constraint: {manifest.platform_version}"
        )
    for perm in manifest.permissions:
        if not isinstance(perm, str) or not perm.strip():
            raise PluginValidationError("Permissions must be non-empty strings")


def validate_plugin_directory(plugin_root: Path) -> None:
    manifest_path = plugin_root / "manifest.yaml"
    if not manifest_path.is_file():
        raise PluginValidationError(f"Missing manifest.yaml in {plugin_root}")

    for dirname in PLUGIN_DIRECTORY_LAYOUT:
        sub = plugin_root / dirname
        if not sub.is_dir():
            sub.mkdir(parents=True, exist_ok=True)


def validate_platform_version(manifest: PluginManifest, platform_version: str) -> None:
    from platform_plugins.plugin_dependencies import version_satisfies

    if not version_satisfies(platform_version, manifest.platform_version):
        raise PluginValidationError(
            f"Plugin {manifest.id} requires platform {manifest.platform_version}, "
            f"running {platform_version}"
        )

# Plugin manifest parsing and schema constants.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from platform_plugins.exceptions import PluginValidationError
from platform_plugins.models import PluginManifest

REQUIRED_MANIFEST_FIELDS = (
    "id",
    "name",
    "version",
    "author",
    "description",
    "platform_version",
    "dependencies",
    "permissions",
    "configuration",
    "routes",
    "workflows",
)

PLUGIN_DIRECTORY_LAYOUT = (
    "workflow",
    "handlers",
    "services",
    "routes",
    "messages",
    "permissions",
    "config",
    "migrations",
    "assets",
)


def load_manifest(path: Path) -> PluginManifest:
    if not path.is_file():
        raise PluginValidationError(f"Manifest not found: {path}")
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise PluginValidationError("Manifest must be a YAML mapping")
    return manifest_from_dict(raw)


def manifest_from_dict(raw: dict[str, Any]) -> PluginManifest:
    missing = [f for f in REQUIRED_MANIFEST_FIELDS if f not in raw]
    if missing:
        raise PluginValidationError(f"Missing manifest fields: {', '.join(missing)}")

    plugin_id = str(raw["id"]).strip()
    if not plugin_id:
        raise PluginValidationError("Plugin id cannot be empty")

    deps = raw.get("dependencies") or {}
    if not isinstance(deps, dict):
        raise PluginValidationError("dependencies must be a mapping")

    return PluginManifest(
        id=plugin_id,
        name=str(raw["name"]),
        version=str(raw["version"]),
        author=str(raw["author"]),
        description=str(raw["description"]),
        platform_version=str(raw["platform_version"]),
        dependencies={
            "required": list(deps.get("required") or []),
            "optional": list(deps.get("optional") or []),
        },
        permissions=list(raw.get("permissions") or []),
        configuration=dict(raw.get("configuration") or {}),
        routes=list(raw.get("routes") or []),
        workflows=list(raw.get("workflows") or []),
        entry_point=raw.get("entry_point"),
        raw=raw,
    )


def manifest_schema() -> dict[str, Any]:
    """JSON-schema-like description for documentation."""
    return {
        "type": "object",
        "required": list(REQUIRED_MANIFEST_FIELDS),
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"},
            "name": {"type": "string"},
            "version": {"type": "string", "description": "Semver"},
            "author": {"type": "string"},
            "description": {"type": "string"},
            "platform_version": {"type": "string", "description": "Semver constraint"},
            "dependencies": {
                "type": "object",
                "properties": {
                    "required": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id"],
                            "properties": {
                                "id": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                    },
                    "optional": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id"],
                            "properties": {
                                "id": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "permissions": {"type": "array", "items": {"type": "string"}},
            "configuration": {"type": "object"},
            "routes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "handler": {"type": "string"},
                    },
                },
            },
            "workflows": {"type": "array", "items": {"type": "string"}},
            "entry_point": {"type": "string", "description": "module:callable for register(ctx)"},
        },
    }

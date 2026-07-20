# Agent metadata and capability validation.

from __future__ import annotations

import re

from platform_agents.exceptions import AgentValidationError
from platform_agents.models import AgentMetadata

AGENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$")

REQUIRED_METADATA_FIELDS = (
    "id",
    "name",
    "description",
    "version",
    "author",
    "capabilities",
)


def validate_agent_id(agent_id: str) -> None:
    if not agent_id or not AGENT_ID_PATTERN.match(agent_id):
        raise AgentValidationError(
            f"Invalid agent id '{agent_id}' — must match ^[a-z][a-z0-9_-]*$"
        )


def validate_capability(capability: str) -> None:
    if not capability or not CAPABILITY_PATTERN.match(capability):
        raise AgentValidationError(
            f"Invalid capability '{capability}' — must match ^[a-z][a-z0-9_]*$"
        )


def validate_capabilities(capabilities: list[str]) -> None:
    if not capabilities:
        raise AgentValidationError("Agent must expose at least one capability")
    if len(capabilities) != len(set(capabilities)):
        raise AgentValidationError("Duplicate capabilities are not allowed")
    for cap in capabilities:
        validate_capability(cap)


def validate_version(version: str) -> None:
    if not version or not SEMVER_PATTERN.match(version):
        raise AgentValidationError(f"Invalid version '{version}' — expected semver (e.g. 1.0.0)")


def validate_metadata(meta: AgentMetadata) -> None:
    if not meta.name.strip():
        raise AgentValidationError("Agent name is required")
    if not meta.description.strip():
        raise AgentValidationError("Agent description is required")
    if not meta.author.strip():
        raise AgentValidationError("Agent author is required")
    validate_agent_id(meta.id)
    validate_version(meta.version)
    validate_capabilities(meta.capabilities)


def validate_plugin_manifest(data: dict) -> AgentMetadata:
    missing = [f for f in REQUIRED_METADATA_FIELDS if f not in data]
    if missing:
        raise AgentValidationError(f"plugin.json missing required fields: {', '.join(missing)}")

    capabilities = data["capabilities"]
    if not isinstance(capabilities, list):
        raise AgentValidationError("capabilities must be a list")

    meta = AgentMetadata(
        id=str(data["id"]),
        name=str(data["name"]),
        description=str(data["description"]),
        version=str(data["version"]),
        author=str(data["author"]),
        capabilities=[str(c) for c in capabilities],
        priority=int(data.get("priority", 0)),
        enabled=bool(data.get("enabled", True)),
        source="plugin",
    )
    validate_metadata(meta)
    return meta

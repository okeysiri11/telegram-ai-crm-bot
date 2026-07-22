from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


FIRMWARE_STACKS = ("ardupilot", "px4", "inav", "betaflight")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FirmwareProject:
    firmware_project_id: str
    name: str
    stack: str
    version: str = ""
    documentation: str = ""
    log_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "firmware_project_id": self.firmware_project_id,
            "name": self.name,
            "stack": self.stack,
            "version": self.version,
            "documentation": self.documentation,
            "log_paths": list(self.log_paths),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ParameterSet:
    parameter_set_id: str
    firmware_project_id: str
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_set_id": self.parameter_set_id,
            "firmware_project_id": self.firmware_project_id,
            "name": self.name,
            "parameters": dict(self.parameters),
            "created_at": self.created_at,
        }


@dataclass
class ParameterTemplate:
    template_id: str
    name: str
    stack: str
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "stack": self.stack,
            "parameters": dict(self.parameters),
            "description": self.description,
            "created_at": self.created_at,
        }


@dataclass
class FirmwareBackup:
    backup_id: str
    firmware_project_id: str
    label: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "firmware_project_id": self.firmware_project_id,
            "label": self.label,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }

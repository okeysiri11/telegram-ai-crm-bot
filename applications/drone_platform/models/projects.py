from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EngineeringProject:
    project_id: str
    name: str
    description: str = ""
    owner: str = ""
    status: str = "active"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "status": self.status,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ProjectVersion:
    version_id: str
    project_id: str
    version: str
    bom: list[dict[str, Any]] = field(default_factory=list)
    cad_references: list[dict[str, Any]] = field(default_factory=list)
    pcb_references: list[dict[str, Any]] = field(default_factory=list)
    wiring_diagrams: list[dict[str, Any]] = field(default_factory=list)
    assembly_instructions: list[str] = field(default_factory=list)
    engineering_docs: list[dict[str, Any]] = field(default_factory=list)
    revision_history: list[dict[str, Any]] = field(default_factory=list)
    engineering_notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "project_id": self.project_id,
            "version": self.version,
            "bom": list(self.bom),
            "cad_references": list(self.cad_references),
            "pcb_references": list(self.pcb_references),
            "wiring_diagrams": list(self.wiring_diagrams),
            "assembly_instructions": list(self.assembly_instructions),
            "engineering_docs": list(self.engineering_docs),
            "revision_history": list(self.revision_history),
            "engineering_notes": list(self.engineering_notes),
            "created_at": self.created_at,
        }

from __future__ import annotations

from typing import Any

from applications.drone_platform.projects.service import ProjectService, project_service
from applications.drone_platform.shared.store import DroneStore, drone_store


class EngineeringService:
    """Engineering workspace facade over projects, BOM, CAD/PCB, and docs."""

    def __init__(
        self,
        store: DroneStore | None = None,
        projects: ProjectService | None = None,
    ) -> None:
        self.store = store or drone_store
        self.projects = projects or project_service

    def workspace_summary(self, project_id: str) -> dict[str, Any]:
        project = self.projects.get_project(project_id)
        versions = self.projects.list_versions(project_id)
        latest = versions[-1] if versions else None
        return {
            "project": project.to_dict(),
            "version_count": len(versions),
            "latest_version": latest.to_dict() if latest else None,
            "capabilities": [
                "bom",
                "cad_references",
                "pcb_references",
                "wiring_diagrams",
                "assembly_instructions",
                "engineering_documentation",
                "revision_history",
                "engineering_notes",
            ],
        }


engineering_service = EngineeringService()

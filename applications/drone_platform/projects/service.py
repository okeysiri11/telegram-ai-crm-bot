from __future__ import annotations

import uuid
from typing import Any

from applications.drone_platform.models.projects import EngineeringProject, ProjectVersion
from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class ProjectService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_project(
        self,
        *,
        name: str,
        description: str = "",
        owner: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> EngineeringProject:
        pid = project_id or f"prj_{uuid.uuid4().hex[:12]}"
        project = EngineeringProject(
            project_id=pid,
            name=name,
            description=description,
            owner=owner,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )
        self.store.projects.save(pid, project)
        return project

    def get_project(self, project_id: str) -> EngineeringProject:
        item = self.store.projects.get(project_id)
        if item is None:
            raise NotFoundError("project", project_id)
        return item

    def list_projects(self) -> list[EngineeringProject]:
        return self.store.projects.list_all()

    def create_version(
        self,
        *,
        project_id: str,
        version: str,
        bom: list[dict[str, Any]] | None = None,
        cad_references: list[dict[str, Any]] | None = None,
        pcb_references: list[dict[str, Any]] | None = None,
        wiring_diagrams: list[dict[str, Any]] | None = None,
        assembly_instructions: list[str] | None = None,
        engineering_docs: list[dict[str, Any]] | None = None,
        engineering_notes: list[str] | None = None,
        version_id: str | None = None,
    ) -> ProjectVersion:
        self.get_project(project_id)
        vid = version_id or f"ver_{uuid.uuid4().hex[:12]}"
        rev = {"version": version, "note": "Initial revision" if not engineering_notes else engineering_notes[0]}
        record = ProjectVersion(
            version_id=vid,
            project_id=project_id,
            version=version,
            bom=list(bom or []),
            cad_references=list(cad_references or []),
            pcb_references=list(pcb_references or []),
            wiring_diagrams=list(wiring_diagrams or []),
            assembly_instructions=list(assembly_instructions or []),
            engineering_docs=list(engineering_docs or []),
            revision_history=[rev],
            engineering_notes=list(engineering_notes or []),
        )
        self.store.project_versions.save(vid, record)
        return record

    def get_version(self, version_id: str) -> ProjectVersion:
        item = self.store.project_versions.get(version_id)
        if item is None:
            raise NotFoundError("project_version", version_id)
        return item

    def list_versions(self, project_id: str | None = None) -> list[ProjectVersion]:
        items = self.store.project_versions.list_all()
        if project_id:
            return [v for v in items if v.project_id == project_id]
        return items

    def add_revision_note(self, version_id: str, note: str) -> ProjectVersion:
        version = self.get_version(version_id)
        version.revision_history.append({"note": note})
        version.engineering_notes.append(note)
        self.store.project_versions.save(version_id, version)
        return version


project_service = ProjectService()

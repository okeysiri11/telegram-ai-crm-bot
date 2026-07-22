"""PCB engineering — KiCad projects, BOM, Gerber, manufacturing packs (Sprint 11.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


COMPONENT_LIBRARY: list[dict[str, Any]] = [
    {"mpn": "STM32H743VIT6", "type": "mcu", "package": "LQFP100"},
    {"mpn": "ICM-42688-P", "type": "imu", "package": "LGA14"},
    {"mpn": "BMP388", "type": "baro", "package": "LGA10"},
    {"mpn": "TPS54560", "type": "regulator", "package": "HTSSOP"},
    {"mpn": "MOSFET-40V", "type": "power", "package": "DFN"},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PCBEngineering:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def component_library(self) -> list[dict[str, Any]]:
        return list(COMPONENT_LIBRARY)

    def create_project(
        self,
        *,
        name: str,
        tool: str = "kicad",
        revision: str = "A",
        components: list[dict[str, Any]] | None = None,
        layers: int = 4,
    ) -> dict[str, Any]:
        if tool.lower() != "kicad" and tool.lower() not in {"kicad", "altium", "eagle"}:
            raise ValidationError(f"Unsupported PCB tool: {tool}")
        pid = f"pcb_{uuid.uuid4().hex[:12]}"
        project = {
            "pcb_project_id": pid,
            "name": name,
            "tool": tool.lower(),
            "revision": revision,
            "layers": layers,
            "components": list(components or []),
            "versions": [{"revision": revision, "at": _now()}],
            "schematic_valid": None,
            "created_at": _now(),
        }
        self.store.pcb_projects.save(pid, project)
        return project

    def pcb_registry(self) -> list[dict[str, Any]]:
        return self.store.pcb_projects.list_all()

    def get(self, pcb_project_id: str) -> dict[str, Any]:
        item = self.store.pcb_projects.get(pcb_project_id)
        if item is None:
            raise NotFoundError("pcb_project", pcb_project_id)
        return item

    def bom_generator(self, pcb_project_id: str) -> dict[str, Any]:
        project = self.get(pcb_project_id)
        bom = []
        for i, c in enumerate(project.get("components") or [], start=1):
            bom.append(
                {
                    "line": i,
                    "ref": c.get("ref", f"U{i}"),
                    "mpn": c.get("mpn", ""),
                    "qty": int(c.get("qty", 1)),
                    "value": c.get("value", ""),
                    "footprint": c.get("footprint", ""),
                }
            )
        return {"pcb_project_id": pcb_project_id, "bom": bom, "line_count": len(bom)}

    def schematic_validator(self, pcb_project_id: str) -> dict[str, Any]:
        project = self.get(pcb_project_id)
        issues = []
        comps = project.get("components") or []
        if not comps:
            issues.append("No components in schematic")
        refs = [c.get("ref") for c in comps if c.get("ref")]
        if len(refs) != len(set(refs)):
            issues.append("Duplicate reference designators")
        project["schematic_valid"] = not issues
        project["schematic_issues"] = issues
        self.store.pcb_projects.save(pcb_project_id, project)
        return {"pcb_project_id": pcb_project_id, "valid": not issues, "issues": issues}

    def version_control(self, pcb_project_id: str, *, revision: str, notes: str = "") -> dict[str, Any]:
        project = self.get(pcb_project_id)
        project["revision"] = revision
        project["versions"].append({"revision": revision, "notes": notes, "at": _now()})
        self.store.pcb_projects.save(pcb_project_id, project)
        return project

    def gerber_export(self, pcb_project_id: str) -> dict[str, Any]:
        project = self.get(pcb_project_id)
        files = [
            f"{project['name']}-F_Cu.gbr",
            f"{project['name']}-B_Cu.gbr",
            f"{project['name']}-Edge_Cuts.gbr",
            f"{project['name']}.drl",
        ]
        export = {"pcb_project_id": pcb_project_id, "format": "gerber", "files": files, "exported_at": _now()}
        project["gerber_export"] = export
        self.store.pcb_projects.save(pcb_project_id, project)
        return export

    def manufacturing_package(self, pcb_project_id: str) -> dict[str, Any]:
        bom = self.bom_generator(pcb_project_id)
        gerber = self.gerber_export(pcb_project_id)
        package = {
            "pcb_project_id": pcb_project_id,
            "includes": ["gerbers", "drill", "bom", "centroid", "readme"],
            "bom_lines": bom["line_count"],
            "gerber_files": gerber["files"],
            "built_at": _now(),
        }
        project = self.get(pcb_project_id)
        project["manufacturing_package"] = package
        self.store.pcb_projects.save(pcb_project_id, project)
        return package

    def status(self) -> dict[str, Any]:
        return {
            "pcb_engineering": "1.0",
            "project_count": self.store.pcb_projects.count(),
            "component_library_count": len(COMPONENT_LIBRARY),
            "kicad_ready": True,
            "capabilities": [
                "kicad_project_manager",
                "pcb_registry",
                "component_library",
                "bom_generator",
                "schematic_validator",
                "pcb_version_control",
                "gerber_export",
                "manufacturing_package",
            ],
        }


pcb_engineering = PCBEngineering()

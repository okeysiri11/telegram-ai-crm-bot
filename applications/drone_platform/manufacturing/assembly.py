"""Assembly manager, lines, templates, work instructions (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_ASSEMBLY_STEPS = [
    "frame_prep",
    "motor_mount",
    "esc_install",
    "fc_install",
    "wiring",
    "prop_install",
    "payload_mount",
    "final_torque",
]


class AssemblyManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_template(
        self,
        *,
        name: str,
        product: str = "multirotor",
        steps: list[str] | None = None,
        revision: str = "A",
    ) -> dict[str, Any]:
        tid = f"tmpl_{uuid.uuid4().hex[:12]}"
        template = {
            "template_id": tid,
            "name": name,
            "product": product,
            "steps": list(steps or DEFAULT_ASSEMBLY_STEPS),
            "revision": revision,
            "created_at": _now(),
        }
        self.store.assembly_templates.save(tid, template)
        return template

    def list_templates(self) -> list[dict[str, Any]]:
        return self.store.assembly_templates.list_all()

    def create_work_instruction(self, *, title: str, steps: list[dict[str, Any]], template_id: str = "") -> dict[str, Any]:
        wid = f"wi_{uuid.uuid4().hex[:12]}"
        item = {
            "instruction_id": wid,
            "title": title,
            "template_id": template_id,
            "steps": list(steps),
            "created_at": _now(),
        }
        self.store.work_instructions.save(wid, item)
        return item

    def list_instructions(self) -> list[dict[str, Any]]:
        return self.store.work_instructions.list_all()

    def start_assembly(
        self,
        *,
        order_id: str,
        template_id: str,
        serial_number: str = "",
        line_name: str = "Line-1",
    ) -> dict[str, Any]:
        template = self.store.assembly_templates.get(template_id)
        if template is None:
            raise NotFoundError("assembly_template", template_id)
        aid = f"asm_{uuid.uuid4().hex[:12]}"
        assembly = {
            "assembly_id": aid,
            "order_id": order_id,
            "template_id": template_id,
            "line": line_name,
            "serial_number": serial_number or f"SN-{uuid.uuid4().hex[:8].upper()}",
            "steps": [{"name": s, "status": "pending"} for s in template["steps"]],
            "status": "in_progress",
            "current_step": 0,
            "created_at": _now(),
        }
        self.store.assemblies.save(aid, assembly)
        return assembly

    def complete_step(self, assembly_id: str, *, notes: str = "") -> dict[str, Any]:
        assembly = self.get(assembly_id)
        idx = int(assembly.get("current_step", 0))
        steps = assembly["steps"]
        if idx >= len(steps):
            raise ValidationError("All assembly steps already completed")
        steps[idx]["status"] = "done"
        steps[idx]["notes"] = notes
        steps[idx]["completed_at"] = _now()
        assembly["current_step"] = idx + 1
        if assembly["current_step"] >= len(steps):
            assembly["status"] = "assembled"
        self.store.assemblies.save(assembly_id, assembly)
        return assembly

    def assembly_line_status(self, line_name: str = "Line-1") -> dict[str, Any]:
        items = [a for a in self.store.assemblies.list_all() if a.get("line") == line_name]
        return {
            "line": line_name,
            "active": len([a for a in items if a.get("status") == "in_progress"]),
            "completed": len([a for a in items if a.get("status") == "assembled"]),
            "assemblies": items,
        }

    def get(self, assembly_id: str) -> dict[str, Any]:
        item = self.store.assemblies.get(assembly_id)
        if item is None:
            raise NotFoundError("assembly", assembly_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.assemblies.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "assembly_manager": "1.0",
            "templates": self.store.assembly_templates.count(),
            "assemblies": self.store.assemblies.count(),
            "work_instructions": self.store.work_instructions.count(),
            "capabilities": [
                "assembly_manager",
                "assembly_line",
                "assembly_templates",
                "work_instructions",
            ],
        }


assembly_manager = AssemblyManager()

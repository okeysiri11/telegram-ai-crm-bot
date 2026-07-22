from __future__ import annotations

import json
import uuid
from typing import Any

from applications.drone_platform.models.firmware import (
    FIRMWARE_STACKS,
    FirmwareBackup,
    FirmwareProject,
    ParameterSet,
    ParameterTemplate,
)
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def supported_stacks(self) -> list[str]:
        return list(FIRMWARE_STACKS)

    def create_project(
        self,
        *,
        name: str,
        stack: str,
        version: str = "",
        documentation: str = "",
        metadata: dict[str, Any] | None = None,
        firmware_project_id: str | None = None,
    ) -> FirmwareProject:
        stack_l = stack.lower()
        if stack_l not in FIRMWARE_STACKS:
            raise ValidationError(f"Unsupported firmware stack: {stack}")
        fid = firmware_project_id or f"fw_{uuid.uuid4().hex[:12]}"
        project = FirmwareProject(
            firmware_project_id=fid,
            name=name,
            stack=stack_l,
            version=version,
            documentation=documentation,
            metadata=dict(metadata or {}),
        )
        self.store.firmware_projects.save(fid, project)
        return project

    def get_project(self, firmware_project_id: str) -> FirmwareProject:
        item = self.store.firmware_projects.get(firmware_project_id)
        if item is None:
            raise NotFoundError("firmware_project", firmware_project_id)
        return item

    def list_projects(self, stack: str | None = None) -> list[FirmwareProject]:
        items = self.store.firmware_projects.list_all()
        if stack:
            return [p for p in items if p.stack == stack.lower()]
        return items

    def catalog(self) -> dict[str, Any]:
        by_stack: dict[str, list[dict[str, Any]]] = {s: [] for s in FIRMWARE_STACKS}
        for p in self.store.firmware_projects.list_all():
            by_stack.setdefault(p.stack, []).append(p.to_dict())
        return {"stacks": list(FIRMWARE_STACKS), "projects_by_stack": by_stack}

    def save_parameters(
        self,
        *,
        firmware_project_id: str,
        name: str,
        parameters: dict[str, Any],
        parameter_set_id: str | None = None,
    ) -> ParameterSet:
        self.get_project(firmware_project_id)
        pid = parameter_set_id or f"par_{uuid.uuid4().hex[:12]}"
        record = ParameterSet(
            parameter_set_id=pid,
            firmware_project_id=firmware_project_id,
            name=name,
            parameters=dict(parameters),
        )
        self.store.parameter_sets.save(pid, record)
        return record

    def get_parameter_set(self, parameter_set_id: str) -> ParameterSet:
        item = self.store.parameter_sets.get(parameter_set_id)
        if item is None:
            raise NotFoundError("parameter_set", parameter_set_id)
        return item

    def compare_parameters(self, left_id: str, right_id: str) -> dict[str, Any]:
        left = self.get_parameter_set(left_id)
        right = self.get_parameter_set(right_id)
        keys = set(left.parameters) | set(right.parameters)
        changed = []
        only_left = []
        only_right = []
        for key in sorted(keys):
            if key in left.parameters and key not in right.parameters:
                only_left.append(key)
            elif key in right.parameters and key not in left.parameters:
                only_right.append(key)
            elif left.parameters[key] != right.parameters[key]:
                changed.append(
                    {
                        "parameter": key,
                        "left": left.parameters[key],
                        "right": right.parameters[key],
                    }
                )
        return {
            "left_id": left_id,
            "right_id": right_id,
            "changed": changed,
            "only_left": only_left,
            "only_right": only_right,
        }

    def backup_parameters(self, parameter_set_id: str, label: str = "backup") -> ParameterSet:
        source = self.get_parameter_set(parameter_set_id)
        return self.save_parameters(
            firmware_project_id=source.firmware_project_id,
            name=f"{source.name}:{label}",
            parameters=dict(source.parameters),
        )

    def restore_parameters(self, parameter_set_id: str, target_name: str = "restored") -> ParameterSet:
        source = self.get_parameter_set(parameter_set_id)
        return self.save_parameters(
            firmware_project_id=source.firmware_project_id,
            name=target_name,
            parameters=dict(source.parameters),
        )

    def create_template(
        self,
        *,
        name: str,
        stack: str,
        parameters: dict[str, Any],
        description: str = "",
        template_id: str | None = None,
    ) -> ParameterTemplate:
        stack_l = stack.lower()
        if stack_l not in FIRMWARE_STACKS:
            raise ValidationError(f"Unsupported firmware stack: {stack}")
        tid = template_id or f"tpl_{uuid.uuid4().hex[:12]}"
        template = ParameterTemplate(
            template_id=tid,
            name=name,
            stack=stack_l,
            parameters=dict(parameters),
            description=description,
        )
        self.store.parameter_templates.save(tid, template)
        return template

    def list_templates(self, stack: str | None = None) -> list[ParameterTemplate]:
        items = self.store.parameter_templates.list_all()
        if stack:
            return [t for t in items if t.stack == stack.lower()]
        return items

    def export_configuration(self, parameter_set_id: str) -> str:
        params = self.get_parameter_set(parameter_set_id)
        return json.dumps(params.to_dict(), indent=2, sort_keys=True)

    def import_configuration(
        self,
        *,
        firmware_project_id: str,
        name: str,
        payload: dict[str, Any] | str,
    ) -> ParameterSet:
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        parameters = data.get("parameters", data)
        if not isinstance(parameters, dict):
            raise ValidationError("Configuration payload must include parameters dict")
        return self.save_parameters(
            firmware_project_id=firmware_project_id,
            name=name,
            parameters=parameters,
        )

    def backup_firmware(
        self,
        *,
        firmware_project_id: str,
        label: str = "firmware-backup",
        payload: dict[str, Any] | None = None,
    ) -> FirmwareBackup:
        project = self.get_project(firmware_project_id)
        bid = f"bck_{uuid.uuid4().hex[:12]}"
        backup = FirmwareBackup(
            backup_id=bid,
            firmware_project_id=firmware_project_id,
            label=label,
            payload=dict(payload or {"version": project.version, "stack": project.stack}),
        )
        self.store.firmware_backups.save(bid, backup)
        return backup

    def restore_firmware(self, backup_id: str) -> FirmwareProject:
        backup = self.store.firmware_backups.get(backup_id)
        if backup is None:
            raise NotFoundError("firmware_backup", backup_id)
        project = self.get_project(backup.firmware_project_id)
        if "version" in backup.payload:
            project.version = str(backup.payload["version"])
        project.metadata["restored_from"] = backup_id
        self.store.firmware_projects.save(project.firmware_project_id, project)
        return project

    def organize_logs(self, firmware_project_id: str, log_paths: list[str]) -> FirmwareProject:
        project = self.get_project(firmware_project_id)
        existing = set(project.log_paths)
        for path in log_paths:
            if path not in existing:
                project.log_paths.append(path)
        self.store.firmware_projects.save(firmware_project_id, project)
        return project

    def update_documentation(self, firmware_project_id: str, documentation: str) -> FirmwareProject:
        project = self.get_project(firmware_project_id)
        project.documentation = documentation
        self.store.firmware_projects.save(firmware_project_id, project)
        return project


firmware_service = FirmwareService()

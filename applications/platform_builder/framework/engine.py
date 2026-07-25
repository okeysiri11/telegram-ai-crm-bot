"""Universal Builder Framework facade — Sprint 28.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.framework.builder_registry import BuilderTypeRegistry
from applications.platform_builder.framework.catalogs import (
    LIFECYCLE,
    UI_COMPONENTS,
    VALIDATION_RULES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.framework.extensions import ExtensionSystem
from applications.platform_builder.framework.lifecycle import LifecycleEngine
from applications.platform_builder.framework.preview import LivePreviewEngine
from applications.platform_builder.framework.sdk import BuilderSDK
from applications.platform_builder.framework.templates import TemplateEngine
from applications.platform_builder.framework.validation import ValidationFramework
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class UniversalBuilderFramework:
    """One common architecture for every Platform Builder."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.lifecycle = LifecycleEngine()
        self.validation = ValidationFramework()
        self.preview_engine = LivePreviewEngine()
        self.registry = BuilderTypeRegistry(self.store)
        self.templates = TemplateEngine(self.store)
        self.extensions = ExtensionSystem(self.store)
        self.sdk = BuilderSDK(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "builder_id": "universal_framework",
            "version": "1.4.0",
            "sprint": "28.5",
            "operational": True,
            "builder_registry_ready": True,
            "template_engine_ready": True,
            "builder_sdk_foundation_ready": True,
            **full_catalog(),
        }

    def bootstrap(self) -> dict[str, Any]:
        seeded = self.registry.seed_known_builders()
        return {
            "ok": True,
            "seeded": seeded,
            "lifecycle": list(LIFECYCLE),
            "bootstrapped_at": _now(),
        }

    def start_session(self) -> dict[str, Any]:
        sid = _id("ubf")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "lifecycle_state": self.lifecycle.start("universal_framework"),
            "draft": {
                "name": "",
                "builder_type": "",
                "version": "1.0.0",
                "components": list(UI_COMPONENTS),
                "validation_rules": [r["id"] for r in VALIDATION_RULES],
                "steps": [s["title"] for s in WIZARD_STEPS],
                "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                "dependencies": ["builder_engine", "help_system"],
                "knowledge_topics": ["builder_framework"],
                "extensions": [],
                "save_as_template": True,
                "brand_color": "#1B6CA8",
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.framework_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.framework_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Framework session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        if "lifecycle_phase" in patch:
            session["lifecycle_state"] = self.lifecycle.run_to(
                session["lifecycle_state"], str(patch["lifecycle_phase"])
            )
        session["updated_at"] = _now()
        self.store.framework_sessions.save(session_id, session)
        return session

    def validate_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        existing = [i.get("name", "") for i in self.registry.list_all()["items"]]
        existing += [t.get("name", "") for t in self.templates.list_all()["items"]]
        return self.validation.validate(
            draft=draft,
            required=["name", "builder_type"],
            existing_names=existing,
            dependencies=list(draft.get("dependencies") or []),
            knowledge_topics=list(draft.get("knowledge_topics") or []),
            relationships={},
            registry_ok=True,
        )

    def preview(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        existing = [i.get("name", "") for i in self.registry.list_all()["items"]]
        return self.preview_engine.preview(session["draft"], existing_names=existing)

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        validation = self.validate_session(session_id)
        return {
            "session_id": session_id,
            "title": "Universal Builder Framework Summary",
            "configuration": {
                "name": draft.get("name"),
                "builder_type": draft.get("builder_type"),
                "version": draft.get("version"),
                "components": draft.get("components") or [],
                "steps": draft.get("steps") or [],
                "schema": draft.get("schema") or {},
            },
            "validation": validation,
            "dependencies": draft.get("dependencies") or [],
            "objects": {
                "builder": draft.get("builder_type"),
                "template": bool(draft.get("save_as_template")),
                "components": len(draft.get("components") or []),
                "schema": bool(draft.get("schema")),
            },
            "registry": self.registry.list_all(),
            "lifecycle": session.get("lifecycle_state"),
            "sdk": self.sdk.foundation(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        name = (draft.get("name") or "").strip()
        builder_type = (draft.get("builder_type") or "").strip()
        if not name:
            raise ValidationError("Builder name is required")
        if not builder_type:
            raise ValidationError("builder_type is required")

        validation = self.validate_session(session_id)
        if not validation["ok"]:
            raise ValidationError(validation["errors"][0]["message"])

        registered_builder = self.registry.register(
            {
                "builder_type": builder_type,
                "name": name,
                "version": draft.get("version") or "1.0.0",
                "schema": draft.get("schema") or {},
                "components": draft.get("components") or [],
                "validation_rules": draft.get("validation_rules") or [],
                "lifecycle": list(LIFECYCLE),
                "status": "registered",
                "source": "universal_builder_framework",
            }
        )

        template = None
        if draft.get("save_as_template", True):
            template = self.templates.save_template(
                {
                    "name": f"{name} Template",
                    "builder_type": builder_type,
                    "config": draft,
                    "components": draft.get("components") or [],
                    "validation_rules": draft.get("validation_rules") or [],
                    "schema": draft.get("schema") or {},
                }
            )
            registered_builder = self.registry.register(
                {
                    **registered_builder,
                    "templates": [template["template_id"]],
                }
            )

        components_record = {
            "components_id": _id("bcomp"),
            "builder_type": builder_type,
            "components": draft.get("components") or [],
            "registered_at": _now(),
        }
        self.store.builder_components.save(components_record["components_id"], components_record)

        schema_record = {
            "schema_id": _id("bschema"),
            "builder_type": builder_type,
            "schema": draft.get("schema") or {},
            "registered_at": _now(),
        }
        self.store.builder_schemas.save(schema_record["schema_id"], schema_record)

        for ext in draft.get("extensions") or []:
            if isinstance(ext, str):
                name = ext
                normalized = ext.lower().replace(" ", "_")
                if normalized.startswith("future_marketplace"):
                    normalized = "marketplace_extensions"
                ext_type = normalized
            else:
                name = ext.get("name") or "extension"
                ext_type = ext.get("extension_type") or "plugins"
            self.extensions.register(
                {
                    "name": name,
                    "extension_type": ext_type,
                    "builder_type": builder_type,
                }
            )

        session["lifecycle_state"] = self.lifecycle.run_to(session["lifecycle_state"], "finish")
        session["status"] = "created"
        session["created_builder_type"] = builder_type
        session["updated_at"] = _now()
        self.store.framework_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "builder": registered_builder,
            "template": template,
            "components": components_record,
            "schema": schema_record,
            "registry": self.registry.list_all(),
            "sdk_foundation": self.sdk.foundation(),
            "message": "Builder, template, components, and schema registered in Builder Registry.",
        }

    def status(self) -> dict[str, Any]:
        if not self.registry.list_all()["count"]:
            self.registry.seed_known_builders()
        return {
            "ready": True,
            "operational": True,
            "wizard_steps": len(WIZARD_STEPS),
            "lifecycle": self.lifecycle.status(),
            "validation": self.validation.status(),
            "preview": self.preview_engine.status(),
            "builder_registry": self.registry.status(),
            "template_engine": self.templates.status(),
            "extensions": self.extensions.status(),
            "sdk": self.sdk.status(),
            "sessions": len(self.store.framework_sessions.list_all()),
        }

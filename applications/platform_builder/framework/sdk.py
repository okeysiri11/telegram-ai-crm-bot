"""Builder SDK foundation — Sprint 28.5."""

from __future__ import annotations

from typing import Any

from applications.platform_builder.framework.builder_registry import BuilderTypeRegistry
from applications.platform_builder.framework.catalogs import LIFECYCLE, SDK_APIS_PLANNED, UI_COMPONENTS
from applications.platform_builder.framework.lifecycle import LifecycleEngine
from applications.platform_builder.framework.templates import TemplateEngine
from applications.platform_builder.framework.validation import ValidationFramework
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


class BuilderSDK:
    """Architecture for future internal Builder SDK — Framework APIs to create new Builders."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.registry = BuilderTypeRegistry(self.store)
        self.templates = TemplateEngine(self.store)
        self.lifecycle = LifecycleEngine()
        self.validation = ValidationFramework()

    def define_builder(self, schema: dict[str, Any]) -> dict[str, Any]:
        return self.registry.register(
            {
                **schema,
                "lifecycle": list(LIFECYCLE),
                "components": schema.get("components") or list(UI_COMPONENTS),
                "source": "builder_sdk",
            }
        )

    def register_steps(self, builder_id: str, steps: list[Any]) -> dict[str, Any]:
        item = self.registry.require(builder_id)
        schema = dict(item.get("schema") or {})
        schema["steps"] = list(steps)
        return self.registry.register({**item, "schema": schema, "source": "builder_sdk"})

    def attach_validation(self, builder_id: str, rules: list[str]) -> dict[str, Any]:
        item = self.registry.require(builder_id)
        return self.registry.register(
            {**item, "validation_rules": list(rules), "source": "builder_sdk"}
        )

    def attach_components(self, builder_id: str, components: list[str]) -> dict[str, Any]:
        item = self.registry.require(builder_id)
        return self.registry.register(
            {**item, "components": list(components), "source": "builder_sdk"}
        )

    def save_template(self, builder_id: str, config: dict[str, Any]) -> dict[str, Any]:
        item = self.registry.require(builder_id)
        return self.templates.save_template(
            {
                "name": config.get("name") or f"{item['name']} Template",
                "builder_type": builder_id,
                "config": config,
                "components": item.get("components") or [],
                "validation_rules": item.get("validation_rules") or [],
                "schema": item.get("schema") or {},
            }
        )

    def clone_builder(self, builder_id: str, *, new_type: str | None = None) -> dict[str, Any]:
        item = self.registry.require(builder_id)
        clone_type = new_type or f"{builder_id}_clone"
        return self.registry.register(
            {
                **item,
                "builder_type": clone_type,
                "name": f"{item['name']} Clone",
                "source": "builder_sdk_clone",
            }
        )

    def run_lifecycle(self, builder_type: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        state = self.lifecycle.start(builder_type, config)
        while state.get("status") != "finished":
            state = self.lifecycle.advance(state)
        return state

    def foundation(self) -> dict[str, Any]:
        return {
            "status": "architecture_only",
            "ready": True,
            "description": "Internal Builder SDK foundation using Universal Builder Framework APIs.",
            "apis": list(SDK_APIS_PLANNED),
            "note": "Full packaged SDK distribution arrives in a later sprint — architecture + callable APIs here.",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "foundation": True,
            "apis": list(SDK_APIS_PLANNED),
            "registry": self.registry.status(),
        }

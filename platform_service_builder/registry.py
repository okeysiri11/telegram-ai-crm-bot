"""Service registry + version store — Sprint 36.0."""

from __future__ import annotations

import time
from typing import Any

from platform_service_builder.dependency import dependency_resolver
from platform_service_builder.models import (
    ServiceConfiguration,
    ServiceDefinition,
    ServiceManifest,
    ServiceState,
    ServiceVersion,
    compare_semver,
)


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, ServiceDefinition] = {}
        self._versions: dict[str, list[ServiceVersion]] = {}

    def reset(self) -> None:
        self._services.clear()
        self._versions.clear()
        dependency_resolver.reset()

    def register(
        self,
        manifest: ServiceManifest | dict[str, Any],
        *,
        configuration: ServiceConfiguration | dict[str, Any] | None = None,
        actor: str = "system",
    ) -> ServiceDefinition:
        mf = manifest if isinstance(manifest, ServiceManifest) else ServiceManifest.from_dict(manifest)
        if mf.id in self._services:
            raise ValueError(f"service already registered: {mf.id}")

        cfg = configuration
        if cfg is None:
            cfg = ServiceConfiguration(settings=dict(mf.settings))
        elif isinstance(cfg, dict):
            cfg = ServiceConfiguration.from_dict(cfg)

        definition = ServiceDefinition(
            id=mf.id,
            manifest=mf,
            state=ServiceState.DRAFT,
            configuration=cfg,
        )
        self._services[mf.id] = definition
        dependency_resolver.set_dependencies(mf.id, list(mf.dependencies))
        self._record_version(definition, actor=actor, changelog="initial registration")
        return definition

    def update(
        self,
        service_id: str,
        *,
        patch: dict[str, Any],
        actor: str = "system",
    ) -> ServiceDefinition:
        definition = self.get(service_id)
        data = definition.manifest.to_dict()
        # nested permissions / healthcheck merge
        for key, value in patch.items():
            if key in {"id", "service_id"}:
                continue
            if key == "permissions" and isinstance(value, dict):
                merged = data.get("permissions") or {}
                merged.update(value)
                data["permissions"] = merged
            elif key == "configuration" and isinstance(value, dict):
                definition.configuration = ServiceConfiguration.from_dict(
                    {**definition.configuration.to_dict(), **value}
                )
            elif key == "enabled":
                definition.enabled = bool(value)
            else:
                data[key] = value

        new_version = str(data.get("version") or definition.manifest.version)
        version_bumped = compare_semver(new_version, definition.manifest.version) != 0
        definition.manifest = ServiceManifest.from_dict(data)
        definition.updated_at = time.time()
        dependency_resolver.set_dependencies(service_id, list(definition.manifest.dependencies))
        if version_bumped:
            self._record_version(definition, actor=actor, changelog=str(patch.get("changelog") or "version update"))
        return definition

    def get(self, service_id: str) -> ServiceDefinition:
        definition = self._services.get(service_id)
        if definition is None:
            raise KeyError(f"service not found: {service_id}")
        return definition

    def get_optional(self, service_id: str) -> ServiceDefinition | None:
        return self._services.get(service_id)

    def list_all(self) -> list[ServiceDefinition]:
        return sorted(self._services.values(), key=lambda s: s.manifest.name.lower())

    def list_by_state(self, *states: ServiceState) -> list[ServiceDefinition]:
        wanted = set(states)
        return [s for s in self.list_all() if s.state in wanted]

    def uninstall(self, service_id: str) -> ServiceDefinition:
        definition = self.get(service_id)
        definition.state = ServiceState.REMOVING
        definition.updated_at = time.time()
        removed = self._services.pop(service_id)
        dependency_resolver.remove(service_id)
        self._versions.pop(service_id, None)
        removed.state = ServiceState.DRAFT
        return removed

    def versions(self, service_id: str) -> list[ServiceVersion]:
        return list(self._versions.get(service_id, []))

    def resolve_version(self, service_id: str, *, version: str | None = None) -> ServiceVersion | None:
        versions = self._versions.get(service_id, [])
        if not versions:
            return None
        if version is None:
            active = next((v for v in versions if v.is_active), None)
            return active or versions[-1]
        for v in versions:
            if v.version == version:
                return v
        return None

    def activate_version(self, service_id: str, version: str) -> ServiceVersion:
        versions = self._versions.get(service_id)
        if not versions:
            raise KeyError(f"no versions for service: {service_id}")
        target = None
        for v in versions:
            v.is_active = v.version == version
            if v.is_active:
                target = v
        if target is None:
            raise KeyError(f"version not found: {service_id}@{version}")
        definition = self.get(service_id)
        definition.manifest = ServiceManifest.from_dict(target.manifest_snapshot)
        definition.updated_at = time.time()
        dependency_resolver.set_dependencies(service_id, list(definition.manifest.dependencies))
        return target

    def _record_version(self, definition: ServiceDefinition, *, actor: str, changelog: str) -> ServiceVersion:
        for existing in self._versions.get(definition.id, []):
            existing.is_active = False
        record = ServiceVersion(
            service_id=definition.id,
            version=definition.manifest.version,
            changelog=changelog,
            created_by=actor,
            manifest_snapshot=definition.manifest.to_dict(),
            is_active=True,
        )
        self._versions.setdefault(definition.id, []).append(record)
        return record


service_registry = ServiceRegistry()

"""Service lifecycle manager — install / load / start / stop / restart / reload / enable."""

from __future__ import annotations

import time
from typing import Any

from platform_service_builder.audit import service_audit
from platform_service_builder.dependency import dependency_resolver
from platform_service_builder.health import health_checker
from platform_service_builder.loader import service_loader
from platform_service_builder.models import ServiceDefinition, ServiceState, VALID_TRANSITIONS
from platform_service_builder.registry import ServiceRegistry
from platform_service_builder.sandbox import service_sandbox


class LifecycleError(RuntimeError):
    pass


class ServiceLifecycleManager:
    def __init__(self, registry: ServiceRegistry) -> None:
        self._registry = registry

    def _transition(self, definition: ServiceDefinition, new_state: ServiceState) -> None:
        current = definition.state
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_state not in allowed and new_state != current:
            raise LifecycleError(
                f"invalid transition {current.value} → {new_state.value} for {definition.id}"
            )
        definition.state = new_state
        definition.manifest.status = new_state.value
        definition.updated_at = time.time()

    def _ensure_deps_ready(self, definition: ServiceDefinition, *, for_start: bool) -> None:
        missing = dependency_resolver.missing_dependencies(
            definition.id,
            {s.id for s in self._registry.list_all()},
        )
        if missing:
            raise LifecycleError(f"missing dependencies: {', '.join(missing)}")
        if dependency_resolver.has_cycle_involving(definition.id):
            raise LifecycleError(f"cyclic dependency involving {definition.id}")
        if for_start:
            for dep_id in dependency_resolver.dependencies_of(definition.id):
                dep = self._registry.get_optional(dep_id)
                if dep is None:
                    raise LifecycleError(f"missing dependency: {dep_id}")
                if not dep.enabled or dep.state == ServiceState.DISABLED:
                    raise LifecycleError(f"disabled dependency: {dep_id}")
                if dep.state not in {ServiceState.RUNNING, ServiceState.LOADED, ServiceState.PAUSED}:
                    raise LifecycleError(
                        f"dependency {dep_id} not ready (state={dep.state.value})"
                    )

    def install(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        try:
            if definition.state == ServiceState.DRAFT:
                self._transition(definition, ServiceState.INSTALLED)
            elif definition.state in {
                ServiceState.INSTALLED,
                ServiceState.LOADED,
                ServiceState.RUNNING,
                ServiceState.PAUSED,
            }:
                pass
            else:
                self._transition(definition, ServiceState.INSTALLED)
            definition.enabled = True
            service_audit.log(
                service_id,
                message="service installed",
                actor=actor,
                operation="install",
                old_state=old,
                new_state=definition.state.value,
                duration_ms=(time.time() - started) * 1000,
                result="ok",
            )
            return definition
        except Exception as exc:
            service_audit.log(
                service_id,
                message=str(exc),
                actor=actor,
                operation="install",
                old_state=old,
                new_state=definition.state.value,
                result="error",
                level="error",
            )
            raise

    def load(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        try:
            if definition.state == ServiceState.DRAFT:
                self.install(service_id, actor=actor)
            self._ensure_deps_ready(definition, for_start=False)
            result = service_loader.load(
                service_id,
                module_path=definition.manifest.module_path,
                entrypoint=definition.manifest.entrypoint,
            )
            definition.loaded_module = result.get("module") or "virtual"
            if definition.sandbox_id:
                service_sandbox.destroy(definition.sandbox_id)
            sbx = service_sandbox.create(
                service_id,
                env=definition.configuration.env,
                resources=definition.configuration.resources,
            )
            definition.sandbox_id = sbx.sandbox_id
            if definition.state != ServiceState.LOADED:
                if definition.state == ServiceState.INSTALLED:
                    self._transition(definition, ServiceState.LOADED)
                elif definition.state in {ServiceState.FAILED, ServiceState.DISABLED}:
                    self._transition(definition, ServiceState.LOADED)
                elif definition.state == ServiceState.RUNNING:
                    pass
                else:
                    self._transition(definition, ServiceState.LOADED)
            service_audit.log(
                service_id,
                message="service loaded",
                actor=actor,
                operation="load",
                old_state=old,
                new_state=definition.state.value,
                duration_ms=(time.time() - started) * 1000,
                details=result,
            )
            return definition
        except Exception as exc:
            definition.error_message = str(exc)
            definition.error_count += 1
            try:
                if definition.state in VALID_TRANSITIONS and ServiceState.FAILED in VALID_TRANSITIONS[definition.state]:
                    self._transition(definition, ServiceState.FAILED)
                else:
                    definition.state = ServiceState.FAILED
                    definition.manifest.status = ServiceState.FAILED.value
            except LifecycleError:
                definition.state = ServiceState.FAILED
            service_audit.log(
                service_id,
                message=str(exc),
                actor=actor,
                operation="load",
                old_state=old,
                new_state=definition.state.value,
                result="error",
                level="error",
            )
            raise

    def start(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        try:
            if not definition.enabled:
                raise LifecycleError(f"service disabled: {service_id}")
            if definition.state in {ServiceState.DRAFT, ServiceState.INSTALLED, ServiceState.FAILED}:
                self.load(service_id, actor=actor)
            self._ensure_deps_ready(definition, for_start=True)
            if definition.state == ServiceState.PAUSED:
                self._transition(definition, ServiceState.RUNNING)
            elif definition.state == ServiceState.LOADED:
                self._transition(definition, ServiceState.RUNNING)
            elif definition.state == ServiceState.RUNNING:
                pass
            else:
                self._transition(definition, ServiceState.RUNNING)
            definition.started_at = time.time()
            definition.error_message = None
            health_checker.heartbeat(definition, response_time_ms=5.0)
            service_audit.log(
                service_id,
                message="service started",
                actor=actor,
                operation="start",
                old_state=old,
                new_state=definition.state.value,
                duration_ms=(time.time() - started) * 1000,
            )
            return definition
        except Exception as exc:
            definition.error_message = str(exc)
            definition.error_count += 1
            definition.state = ServiceState.FAILED
            definition.manifest.status = ServiceState.FAILED.value
            service_audit.log(
                service_id,
                message=str(exc),
                actor=actor,
                operation="start",
                old_state=old,
                new_state=definition.state.value,
                result="error",
                level="error",
            )
            raise

    def stop(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        # stop dependents first conceptually — caller may use shutdown order
        if definition.state == ServiceState.RUNNING:
            self._transition(definition, ServiceState.LOADED)
        elif definition.state == ServiceState.PAUSED:
            self._transition(definition, ServiceState.LOADED)
        definition.started_at = None
        service_audit.log(
            service_id,
            message="service stopped",
            actor=actor,
            operation="stop",
            old_state=old,
            new_state=definition.state.value,
            duration_ms=(time.time() - started) * 1000,
        )
        return definition

    def pause(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        definition = self._registry.get(service_id)
        old = definition.state.value
        self._transition(definition, ServiceState.PAUSED)
        service_audit.log(
            service_id,
            message="service paused",
            actor=actor,
            operation="pause",
            old_state=old,
            new_state=definition.state.value,
        )
        return definition

    def restart(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        if definition.state in {ServiceState.RUNNING, ServiceState.PAUSED, ServiceState.LOADED}:
            self.stop(service_id, actor=actor)
        definition.restart_count += 1
        result = self.start(service_id, actor=actor)
        service_audit.log(
            service_id,
            message="service restarted",
            actor=actor,
            operation="restart",
            old_state=old,
            new_state=result.state.value,
            duration_ms=(time.time() - started) * 1000,
            details={"restart_count": result.restart_count},
        )
        return result

    def reload(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        was_running = definition.state == ServiceState.RUNNING
        if was_running:
            self.stop(service_id, actor=actor)
        result = service_loader.reload(
            service_id,
            module_path=definition.manifest.module_path,
            entrypoint=definition.manifest.entrypoint,
        )
        definition.loaded_module = result.get("module") or "virtual"
        if definition.state != ServiceState.LOADED:
            if definition.state == ServiceState.INSTALLED:
                self._transition(definition, ServiceState.LOADED)
            elif definition.state in VALID_TRANSITIONS.get(definition.state, set()) and ServiceState.LOADED in VALID_TRANSITIONS[definition.state]:
                self._transition(definition, ServiceState.LOADED)
            else:
                definition.state = ServiceState.LOADED
                definition.manifest.status = ServiceState.LOADED.value
        if was_running:
            self.start(service_id, actor=actor)
        service_audit.log(
            service_id,
            message="service reloaded",
            actor=actor,
            operation="reload",
            old_state=old,
            new_state=definition.state.value,
            duration_ms=(time.time() - started) * 1000,
            details=result,
        )
        return definition

    def enable(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        definition = self._registry.get(service_id)
        old = definition.state.value
        definition.enabled = True
        if definition.state == ServiceState.DISABLED:
            self._transition(definition, ServiceState.INSTALLED)
        service_audit.log(
            service_id,
            message="service enabled",
            actor=actor,
            operation="enable",
            old_state=old,
            new_state=definition.state.value,
        )
        return definition

    def disable(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        definition = self._registry.get(service_id)
        old = definition.state.value
        if definition.state in {ServiceState.RUNNING, ServiceState.PAUSED}:
            self.stop(service_id, actor=actor)
        definition.enabled = False
        if definition.state in VALID_TRANSITIONS.get(definition.state, set()) and ServiceState.DISABLED in VALID_TRANSITIONS[definition.state]:
            self._transition(definition, ServiceState.DISABLED)
        else:
            definition.state = ServiceState.DISABLED
            definition.manifest.status = ServiceState.DISABLED.value
        service_audit.log(
            service_id,
            message="service disabled",
            actor=actor,
            operation="disable",
            old_state=old,
            new_state=definition.state.value,
        )
        return definition

    def uninstall(self, service_id: str, *, actor: str = "system") -> dict[str, Any]:
        started = time.time()
        definition = self._registry.get(service_id)
        old = definition.state.value
        dependents = dependency_resolver.dependents_of(service_id)
        running_deps = [
            d
            for d in dependents
            if (dep := self._registry.get_optional(d))
            and dep.state in {ServiceState.RUNNING, ServiceState.LOADED, ServiceState.PAUSED}
        ]
        if running_deps:
            raise LifecycleError(
                f"cannot uninstall {service_id}; dependents still active: {', '.join(running_deps)}"
            )
        if definition.state in {ServiceState.RUNNING, ServiceState.PAUSED, ServiceState.LOADED}:
            self.stop(service_id, actor=actor)
        service_loader.unload(service_id)
        if definition.sandbox_id:
            service_sandbox.destroy(definition.sandbox_id)
        removed = self._registry.uninstall(service_id)
        service_audit.log(
            service_id,
            message="service uninstalled",
            actor=actor,
            operation="uninstall",
            old_state=old,
            new_state="removed",
            duration_ms=(time.time() - started) * 1000,
        )
        return {"id": service_id, "removed": True, "previous_state": old, "manifest": removed.manifest.to_dict()}

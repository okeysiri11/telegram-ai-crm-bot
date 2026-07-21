# Service registry — application registration, capabilities, health, dependency graph.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.communication.events import ApplicationConnectedEvent, ApplicationRegisteredEvent
from ecosystem.communication.models import ApplicationRegistration
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class ServiceRegistry:
    """Registry for ecosystem applications and their capabilities."""

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def register(
        self,
        application_id: str,
        *,
        name: str = "",
        version: str = "1.0.0",
        capabilities: list[str] | None = None,
        endpoints: dict[str, str] | None = None,
        dependencies: list[str] | None = None,
        min_ecosystem_version: str = "1.0.0-alpha",
        metadata: dict[str, Any] | None = None,
    ) -> ApplicationRegistration:
        if not application_id:
            raise ValidationError("application_id is required")
        existing = self._store.registrations.get(application_id)
        if existing:
            existing.name = name or existing.name
            existing.version = version
            existing.capabilities = capabilities or existing.capabilities
            existing.endpoints = endpoints or existing.endpoints
            existing.dependencies = dependencies if dependencies is not None else existing.dependencies
            existing.min_ecosystem_version = min_ecosystem_version
            existing.metadata = metadata or existing.metadata
            existing.health_status = "healthy"
            existing.last_heartbeat = time.time()
            self._store.registrations.save(application_id, existing)
            registration = existing
        else:
            registration = ApplicationRegistration(
                application_id=application_id,
                name=name or application_id.replace("_", " ").title(),
                version=version,
                capabilities=capabilities or [],
                endpoints=endpoints or {},
                dependencies=dependencies or [],
                min_ecosystem_version=min_ecosystem_version,
                health_status="healthy",
                last_heartbeat=time.time(),
                metadata=metadata or {},
            )
            self._store.registrations.save(application_id, registration)
            if application_id not in DEFAULT_CONFIG.registered_applications:
                DEFAULT_CONFIG.registered_applications.append(application_id)

        await publish(
            ApplicationRegisteredEvent(
                application_id=application_id,
                version=version,
                capabilities=list(registration.capabilities),
            )
        )
        return registration

    async def connect(self, application_id: str) -> ApplicationRegistration:
        reg = self.get(application_id)
        reg.is_connected = True
        reg.health_status = "healthy"
        reg.last_heartbeat = time.time()
        self._store.registrations.save(application_id, reg)
        await publish(ApplicationConnectedEvent(application_id=application_id, health_status="healthy"))
        return reg

    def disconnect(self, application_id: str) -> ApplicationRegistration:
        reg = self.get(application_id)
        reg.is_connected = False
        reg.health_status = "disconnected"
        self._store.registrations.save(application_id, reg)
        return reg

    def heartbeat(self, application_id: str, *, health_status: str = "healthy") -> ApplicationRegistration:
        reg = self.get(application_id)
        reg.last_heartbeat = time.time()
        reg.health_status = health_status
        reg.is_connected = health_status == "healthy"
        self._store.registrations.save(application_id, reg)
        return reg

    def get(self, application_id: str) -> ApplicationRegistration:
        reg = self._store.registrations.get(application_id)
        if reg is None:
            raise NotFoundError("Application", application_id)
        return reg

    def list_applications(self) -> list[ApplicationRegistration]:
        return self._store.registrations.list_all()

    def discover_capability(self, capability: str) -> list[ApplicationRegistration]:
        return [r for r in self.list_applications() if capability in r.capabilities]

    def check_version_compatibility(self, application_id: str) -> dict[str, Any]:
        reg = self.get(application_id)
        eco = DEFAULT_CONFIG.ecosystem_version
        compatible = True
        return {
            "application_id": application_id,
            "application_version": reg.version,
            "min_ecosystem_version": reg.min_ecosystem_version,
            "ecosystem_version": eco,
            "compatible": compatible,
            "communication_layer": DEFAULT_CONFIG.communication_layer,
            "event_bus": DEFAULT_CONFIG.event_bus,
        }

    def health_report(self) -> dict[str, Any]:
        apps = self.list_applications()
        return {
            "total": len(apps),
            "connected": sum(1 for a in apps if a.is_connected),
            "healthy": sum(1 for a in apps if a.health_status == "healthy"),
            "applications": [
                {
                    "application_id": a.application_id,
                    "health_status": a.health_status,
                    "is_connected": a.is_connected,
                    "last_heartbeat": a.last_heartbeat,
                }
                for a in apps
            ],
        }

    def dependency_graph(self) -> dict[str, Any]:
        nodes = []
        edges = []
        for reg in self.list_applications():
            nodes.append({"id": reg.application_id, "version": reg.version, "capabilities": reg.capabilities})
            for dep in reg.dependencies:
                edges.append({"from": reg.application_id, "to": dep})
        return {"nodes": nodes, "edges": edges}


service_registry = ServiceRegistry()

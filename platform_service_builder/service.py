"""Enterprise Service Builder facade — Sprint 36.0."""

from __future__ import annotations

from typing import Any

from platform_service_builder.audit import service_audit
from platform_service_builder.dependency import dependency_resolver
from platform_service_builder.health import health_checker
from platform_service_builder.lifecycle import ServiceLifecycleManager
from platform_service_builder.loader import service_loader
from platform_service_builder.models import (
    ServiceConfiguration,
    ServiceDefinition,
    ServiceManifest,
    ServiceState,
)
from platform_service_builder.permissions import permission_resolver
from platform_service_builder.registry import ServiceRegistry, service_registry
from platform_service_builder.sandbox import service_sandbox


FOUNDATION_CATALOG: list[dict[str, Any]] = [
    {
        "id": "svc_event_bus",
        "name": "event_bus",
        "display_name": "Event Bus Runtime",
        "version": "1.0.0",
        "description": "Canonical platform event bus foundation for all runtimes.",
        "owner": "platform",
        "category": "event",
        "icon": "zap",
        "dependencies": [],
        "api": ["/events", "/events/publish"],
        "events": ["platform.*"],
        "permissions": {
            "allowed_apis": ["events.*", "/events*"],
            "allowed_events": ["platform.*"],
            "allowed_storage": ["events"],
            "allowed_ai_tools": [],
            "allowed_integrations": ["event_bus"],
        },
        "tags": ["foundation", "runtime"],
    },
    {
        "id": "svc_workflow_runtime",
        "name": "workflow_runtime",
        "display_name": "Workflow Runtime",
        "version": "1.0.0",
        "description": "Workflow execution runtime built on Event Bus.",
        "owner": "platform",
        "category": "workflow",
        "icon": "git-branch",
        "dependencies": ["svc_event_bus"],
        "api": ["/workflows", "/workflows/execute"],
        "events": ["workflow.*"],
        "permissions": {
            "allowed_apis": ["workflows.*"],
            "allowed_events": ["workflow.*", "platform.*"],
            "allowed_storage": ["workflows"],
            "allowed_ai_tools": [],
            "allowed_integrations": ["workflow"],
        },
        "tags": ["foundation", "runtime"],
    },
    {
        "id": "svc_ai_runtime",
        "name": "ai_runtime",
        "display_name": "AI Runtime",
        "version": "1.0.0",
        "description": "AI inference and agent execution runtime.",
        "owner": "platform",
        "category": "ai",
        "icon": "brain",
        "dependencies": ["svc_event_bus"],
        "api": ["/ai", "/ai/invoke"],
        "events": ["ai.*"],
        "permissions": {
            "allowed_apis": ["ai.*"],
            "allowed_events": ["ai.*", "platform.*"],
            "allowed_storage": ["ai_memory"],
            "allowed_ai_tools": ["*"],
            "allowed_integrations": ["openai", "anthropic"],
        },
        "tags": ["foundation", "runtime", "ai"],
    },
    {
        "id": "svc_voice_runtime",
        "name": "voice_runtime",
        "display_name": "Voice Command Center",
        "version": "1.0.0",
        "description": "Enterprise voice command runtime — STT, NLU, secure command execution.",
        "owner": "platform",
        "category": "ai",
        "icon": "mic",
        "dependencies": ["svc_event_bus", "svc_ai_runtime", "svc_context_engine"],
        "api": ["/voice", "/voice/process", "/voice-runtime"],
        "events": ["voice.*"],
        "permissions": {
            "allowed_apis": ["voice.*", "ai.*", "context.*", "workflow.*"],
            "allowed_events": ["voice.*", "ai.*", "platform.*"],
            "allowed_storage": ["voice_sessions", "voice_commands"],
            "allowed_ai_tools": [],
            "allowed_integrations": [
                "ai_runtime",
                "workflow_runtime",
                "context_engine",
                "service_builder",
            ],
        },
        "tags": ["foundation", "runtime", "ai", "voice"],
    },
    {
        "id": "svc_context_engine",
        "name": "context_engine",
        "display_name": "Enterprise Context Engine",
        "version": "1.0.0",
        "description": "Collects, merges, and delivers contextual information to AI, Workflows, and Services.",
        "owner": "platform",
        "category": "ai",
        "icon": "layers",
        "dependencies": ["svc_event_bus", "svc_ai_runtime", "svc_project_memory"],
        "api": ["/context", "/context/resolve"],
        "events": ["context.*"],
        "permissions": {
            "allowed_apis": ["context.*", "ai.*", "memory.*"],
            "allowed_events": ["context.*", "ai.*", "memory.*", "platform.*"],
            "allowed_storage": ["ai_memory", "context_cache", "project_memory"],
            "allowed_ai_tools": [],
            "allowed_integrations": ["ai_runtime", "workflow_runtime", "project_memory"],
        },
        "tags": ["foundation", "runtime", "ai", "context"],
    },
    {
        "id": "svc_project_memory",
        "name": "project_memory",
        "display_name": "Project Memory Engine",
        "version": "1.0.0",
        "description": "Long-term semantic memory for projects, agents, clients, workflows, and documents.",
        "owner": "platform",
        "category": "ai",
        "icon": "brain",
        "dependencies": ["svc_event_bus"],
        "api": ["/project-memory", "/memory", "/memory/search"],
        "events": ["memory.*"],
        "permissions": {
            "allowed_apis": ["memory.*", "project-memory.*"],
            "allowed_events": ["memory.*", "platform.*"],
            "allowed_storage": ["project_memory", "memory_embeddings"],
            "allowed_ai_tools": [],
            "allowed_integrations": ["ai_runtime", "context_engine", "workflow_runtime"],
        },
        "tags": ["foundation", "runtime", "ai", "memory"],
    },
    {
        "id": "svc_multi_agent_runtime",
        "name": "multi_agent_runtime",
        "display_name": "Multi-Agent Runtime",
        "version": "1.0.0",
        "description": "Coordinated multi-agent orchestration runtime.",
        "owner": "platform",
        "category": "ai",
        "icon": "users",
        "dependencies": [
            "svc_ai_runtime",
            "svc_workflow_runtime",
            "svc_context_engine",
            "svc_project_memory",
            "svc_voice_runtime",
        ],
        "api": ["/agents", "/agents/orchestrate", "/multi-agent"],
        "events": ["agent.*", "multi_agent.*"],
        "permissions": {
            "allowed_apis": ["agents.*", "ai.*", "context.*", "memory.*", "voice.*", "workflow.*"],
            "allowed_events": ["agent.*", "ai.*", "workflow.*", "context.*", "memory.*", "voice.*"],
            "allowed_storage": ["agents", "ai_memory", "project_memory", "agent_sessions"],
            "allowed_ai_tools": ["*"],
            "allowed_integrations": [
                "ai_runtime",
                "context_engine",
                "project_memory",
                "voice_runtime",
                "workflow_runtime",
            ],
        },
        "tags": ["foundation", "runtime", "ai", "multi-agent"],
    },
    {
        "id": "svc_skills_sdk",
        "name": "skills_sdk",
        "display_name": "AI Skills & SDK",
        "version": "1.0.0",
        "description": "Register, publish, install and execute reusable AI skills with multi-language SDKs.",
        "owner": "platform",
        "category": "ai",
        "icon": "puzzle",
        "dependencies": ["svc_ai_runtime", "svc_multi_agent_runtime"],
        "api": ["/skills", "/sdk", "/skills/execute"],
        "events": ["skill.*"],
        "permissions": {
            "allowed_apis": ["skills.*", "sdk.*", "ai.*", "agents.*"],
            "allowed_events": ["skill.*", "ai.*", "agent.*"],
            "allowed_storage": ["skills", "installed_skills", "skill_marketplace"],
            "allowed_ai_tools": ["*"],
            "allowed_integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "context_engine",
                "project_memory",
                "voice_runtime",
                "workflow_runtime",
            ],
        },
        "tags": ["foundation", "runtime", "ai", "skills", "sdk"],
    },
    {
        "id": "svc_creative_factory",
        "name": "creative_factory",
        "display_name": "Creative Factory",
        "version": "1.0.0",
        "description": "Enterprise Creative Factory — studio, media, campaigns, brand, library, publishing.",
        "owner": "platform",
        "category": "creative",
        "icon": "sparkles",
        "dependencies": [
            "svc_ai_runtime",
            "svc_multi_agent_runtime",
            "svc_skills_sdk",
            "svc_event_bus",
        ],
        "api": [
            "/api/creative",
            "/api/campaigns",
            "/api/media",
            "/management/v1/creative",
        ],
        "events": ["creative.*", "campaign.*", "media.*"],
        "permissions": {
            "allowed_apis": ["creative.*", "campaigns.*", "media.*", "ai.*"],
            "allowed_events": ["creative.*", "campaign.*", "media.*", "ai.*"],
            "allowed_storage": [
                "creative_projects",
                "creative_assets",
                "creative_templates",
                "campaigns",
                "media_library",
                "brand_profiles",
            ],
            "allowed_ai_tools": ["text.*", "image.*", "video.*", "voice.*", "tts.*", "stt.*"],
            "allowed_integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "project_memory",
                "context_engine",
                "workflow_runtime",
                "event_bus",
                "voice_runtime",
                "skills_sdk",
            ],
        },
        "tags": ["foundation", "creative", "marketing", "ai"],
    },
    {
        "id": "svc_enterprise_city",
        "name": "enterprise_city_runtime",
        "display_name": "Enterprise City Runtime",
        "version": "1.0.0",
        "description": "Unified Enterprise City Runtime — kernel, workspace, search, dashboard, command center.",
        "owner": "platform",
        "category": "city",
        "icon": "building",
        "dependencies": [
            "svc_multi_agent_runtime",
            "svc_event_bus",
            "svc_ai_runtime",
            "svc_creative_factory",
            "svc_skills_sdk",
        ],
        "api": [
            "/api/platform",
            "/api/dashboard",
            "/api/search",
            "/management/v1/platform",
            "/city",
            "/city/simulate",
        ],
        "events": ["city.*", "platform.*"],
        "permissions": {
            "allowed_apis": ["platform.*", "dashboard.*", "search.*", "city.*"],
            "allowed_events": ["city.*", "platform.*", "agent.*", "ai.*"],
            "allowed_storage": [
                "platform_registry",
                "platform_sessions",
                "platform_metrics",
                "platform_health",
                "platform_usage",
                "platform_configuration",
            ],
            "allowed_ai_tools": ["*"],
            "allowed_integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "project_memory",
                "context_engine",
                "workflow_runtime",
                "creative_factory",
                "voice_runtime",
                "skills_sdk",
                "event_bus",
                "digital_twin",
            ],
        },
        "tags": ["foundation", "city", "platform", "kernel"],
    },
]


class ServiceBuilderService:
    """
    Enterprise Service Builder — install/configure/version/deploy platform services
    without modifying platform core.
    """

    def __init__(self, registry: ServiceRegistry | None = None) -> None:
        self.registry = registry or service_registry
        self.lifecycle = ServiceLifecycleManager(self.registry)
        self.dependencies = dependency_resolver
        self.loader = service_loader
        self.sandbox = service_sandbox
        self.health = health_checker
        self.permissions = permission_resolver
        self.audit = service_audit
        self._seeded = False

    def reset(self) -> None:
        self.registry.reset()
        self.loader.reset()
        self.sandbox.reset()
        self.health.reset()
        self.audit.reset()
        self._seeded = False

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        for item in FOUNDATION_CATALOG:
            if self.registry.get_optional(item["id"]) is None:
                self.registry.register(item, actor="system")
        self._seeded = True

    def status(self) -> dict[str, Any]:
        self.ensure_seed()
        services = self.registry.list_all()
        by_state: dict[str, int] = {}
        for s in services:
            by_state[s.state.value] = by_state.get(s.state.value, 0) + 1
        return {
            "module": "platform_service_builder",
            "sprint": "36.0",
            "services": len(services),
            "by_state": by_state,
            "startup_order": self.dependencies.resolve_startup_order([s.id for s in services]),
            "cycles": self.dependencies.detect_cycles(),
        }

    # --- CRUD ---

    def create(self, payload: dict[str, Any], *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.registry.register(payload, actor=actor)

    def get(self, service_id: str) -> ServiceDefinition:
        self.ensure_seed()
        return self.registry.get(service_id)

    def list_services(
        self,
        *,
        state: str | None = None,
        category: str | None = None,
        installed_only: bool = False,
        running_only: bool = False,
    ) -> list[ServiceDefinition]:
        self.ensure_seed()
        services = self.registry.list_all()
        if state:
            services = [s for s in services if s.state.value == state]
        if category:
            services = [s for s in services if s.manifest.category == category]
        if installed_only:
            services = [
                s
                for s in services
                if s.state
                in {
                    ServiceState.INSTALLED,
                    ServiceState.LOADED,
                    ServiceState.RUNNING,
                    ServiceState.PAUSED,
                    ServiceState.FAILED,
                    ServiceState.DISABLED,
                    ServiceState.UPDATING,
                }
            ]
        if running_only:
            services = [s for s in services if s.state == ServiceState.RUNNING]
        return services

    def update(self, service_id: str, patch: dict[str, Any], *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.registry.update(service_id, patch=patch, actor=actor)

    def delete(self, service_id: str, *, actor: str = "system") -> dict[str, Any]:
        self.ensure_seed()
        return self.lifecycle.uninstall(service_id, actor=actor)

    # --- lifecycle ---

    def install(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.install(service_id, actor=actor)

    def load(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.load(service_id, actor=actor)

    def start(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        # start dependencies first
        order = self.dependencies.resolve_startup_order([service_id])
        for dep_id in order:
            if dep_id == service_id:
                continue
            dep = self.registry.get_optional(dep_id)
            if dep and dep.state != ServiceState.RUNNING:
                self.lifecycle.start(dep_id, actor=actor)
        return self.lifecycle.start(service_id, actor=actor)

    def stop(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.stop(service_id, actor=actor)

    def restart(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.restart(service_id, actor=actor)

    def reload(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.reload(service_id, actor=actor)

    def enable(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.enable(service_id, actor=actor)

    def disable(self, service_id: str, *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.lifecycle.disable(service_id, actor=actor)

    # --- health / logs / deps / versions / permissions ---

    def health_of(self, service_id: str, *, probe: bool = True) -> dict[str, Any]:
        self.ensure_seed()
        definition = self.registry.get(service_id)
        snap = self.health.heartbeat(definition) if probe else self.health.snapshot(definition)
        return snap.to_dict()

    def health_monitor(self) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [self.health.snapshot(s).to_dict() for s in self.registry.list_all()]

    def logs(self, service_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [e.to_dict() for e in self.audit.for_service(service_id, limit=limit)]

    def dependency_graph(self, service_id: str | None = None) -> dict[str, Any]:
        self.ensure_seed()
        definitions = {s.id: s for s in self.registry.list_all()}
        if service_id:
            node = self.dependencies.graph(service_id, definitions=definitions)
            return {
                "root": service_id,
                "graph": node.to_dict(),
                "startup_order": self.dependencies.resolve_startup_order([service_id]),
                "shutdown_order": self.dependencies.resolve_shutdown_order([service_id]),
                "cycles": self.dependencies.detect_cycles(),
            }
        graphs = {
            sid: self.dependencies.graph(sid, definitions=definitions).to_dict()
            for sid in definitions
        }
        return {
            "graphs": graphs,
            "startup_order": self.dependencies.resolve_startup_order(),
            "shutdown_order": self.dependencies.resolve_shutdown_order(),
            "cycles": self.dependencies.detect_cycles(),
        }

    def versions(self, service_id: str) -> list[dict[str, Any]]:
        self.ensure_seed()
        return [v.to_dict() for v in self.registry.versions(service_id)]

    def configure(self, service_id: str, configuration: dict[str, Any], *, actor: str = "system") -> ServiceDefinition:
        self.ensure_seed()
        return self.registry.update(service_id, patch={"configuration": configuration}, actor=actor)

    def permissions_of(self, service_id: str) -> dict[str, Any]:
        self.ensure_seed()
        definition = self.registry.get(service_id)
        return definition.manifest.permissions.to_dict()

    def check_permission(
        self,
        service_id: str,
        *,
        api: str | None = None,
        event: str | None = None,
        storage: str | None = None,
        ai_tool: str | None = None,
        integration: str | None = None,
    ) -> dict[str, Any]:
        self.ensure_seed()
        definition = self.registry.get(service_id)
        checks = self.permissions.evaluate(
            definition,
            api=api,
            event=event,
            storage=storage,
            ai_tool=ai_tool,
            integration=integration,
        )
        return {"service_id": service_id, "checks": checks, "allowed": all(checks.values()) if checks else False}


service_builder = ServiceBuilderService()

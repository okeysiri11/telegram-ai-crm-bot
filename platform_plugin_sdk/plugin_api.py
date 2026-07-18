# Typed public API facades — stable interfaces hiding Platform Core.

from __future__ import annotations

from typing import Any, Protocol


class EventsApi:
    """Publish and subscribe to platform events."""

    async def publish(self, event: Any) -> None:
        from events.event_bus import PlatformEventBus

        await PlatformEventBus.publish(event, wait=False)

    def subscribe(self, event_type: type | str, handler: Any, *, handler_id: str | None = None) -> str:
        from events.event_bus import PlatformEventBus

        return PlatformEventBus.subscribe(event_type, handler, handler_id=handler_id)


class JobsApi:
    """Schedule background work through the Job Engine."""

    async def enqueue(self, handler_name: str, payload: dict[str, Any], **options: Any) -> dict[str, Any]:
        from platform_jobs.job_engine import job_engine

        job = await job_engine.enqueue(handler_name, payload, **options)
        return job.to_dict() if hasattr(job, "to_dict") else {"job_id": str(job.id)}

    def register_handler(self, name: str, handler: Any) -> None:
        from platform_jobs.job_engine import job_engine

        job_engine.register_handler(name, handler)


class WorkflowApi:
    """Access workflow definitions and execution."""

    def list_definitions(self) -> list[str]:
        from platform_sdk.workflow_loader import sdk_workflow_loader

        sdk_workflow_loader.ensure_loaded()
        from workflow.workflow_registry import workflow_registry

        return list(workflow_registry.list_ids())

    async def run(self, workflow_name: str, **variables: Any) -> dict[str, Any]:
        from workflow import workflow_engine

        vertical = str(variables.pop("vertical", workflow_name.split("_")[0])).upper()
        ctx = await workflow_engine.run_backend_workflow(
            vertical,
            telegram_user=variables.get("telegram_user"),
            request=variables.get("request"),
            manager=variables.get("manager"),
            variables=variables,
        )
        if ctx is None:
            return {"execution_id": None, "workflow": workflow_name}
        return {"execution_id": ctx.execution_id, "status": str(ctx.status)}


class ConfigurationApi:
    """Read platform configuration (not plugin-private config)."""

    def get(self, key: str, default: Any = None) -> Any:
        from platform_configuration.config_provider import config_provider

        return config_provider.get(key, default)

    def is_feature_enabled(self, flag: str) -> bool:
        from platform_configuration.config_provider import config_provider

        return config_provider.is_feature_enabled(flag)


class IamApi:
    """Identity and authorization checks."""

    async def authorize(self, principal: Any, permission: str) -> bool:
        from platform_identity.identity_service import identity_service

        return await identity_service.authorize(principal, permission)

    async def authenticate_telegram(self, telegram_id: int) -> Any:
        from platform_identity.identity_service import identity_service

        return await identity_service.authenticate_telegram(telegram_id)


class IntegrationsApi:
    """Invoke external integrations through the Integration Hub."""

    async def invoke(self, provider: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from platform_integrations.integration_service import integration_service

        result = await integration_service.invoke_by_provider(provider, action, payload)
        return result if isinstance(result, dict) else {"result": result}


class ObservabilityApi:
    """Metrics and telemetry."""

    def increment(self, name: str, value: float = 1.0, **tags: str) -> None:
        from platform_observability.metrics_service import metrics_service

        metrics_service.record(name, value, tags=tags)

    def gauge(self, name: str, value: float, **tags: str) -> None:
        from platform_observability.metrics_service import metrics_service

        metrics_service.record(name, value, unit="gauge", tags=tags)


class ManagementApi:
    """Management API path metadata (no direct HTTP from plugins)."""

    PREFIX = "/management"

    @classmethod
    def path(cls, resource: str) -> str:
        return f"{cls.PREFIX}/{resource.lstrip('/')}"


class SdkApi:
    """Platform SDK for vertical operations."""

    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    def create_context(self, **metadata: Any) -> Any:
        from platform_sdk.vertical_builder import vertical_builder

        return vertical_builder.create_context(plugin_id=self._plugin_id, **metadata)


class AiSkillsApi:
    """Invoke AI Skills — plugins must not call LLM providers directly."""

    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    async def execute(
        self,
        skill_id: str,
        input: dict[str, Any] | None = None,
        *,
        user_id: str | None = None,
        use_cache: bool = True,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from platform_ai.skills.models import SkillExecutionRequest
        from platform_ai.skills.skill_manager import skill_manager

        request = SkillExecutionRequest(
            skill_id=skill_id,
            input=dict(input or {}),
            plugin_id=self._plugin_id,
            user_id=user_id,
            use_cache=use_cache,
        )
        result = await skill_manager.execute(request, extra_context=context)
        return result.to_dict()

    def list_skills(self) -> list[dict[str, Any]]:
        from platform_ai.skills.skill_manager import skill_manager

        return skill_manager.list_skills()


class AiApi:
    """AI Platform access for plugins — skills only, no direct provider calls."""

    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id
        self._skills: AiSkillsApi | None = None

    @property
    def skills(self) -> AiSkillsApi:
        if self._skills is None:
            self._skills = AiSkillsApi(self._plugin_id)
        return self._skills


class RealtimeApiProtocol(Protocol):
    async def publish_widget_update(self, widget_id: str, data: dict[str, Any]) -> None: ...
    async def publish_channel_event(self, channel: str, event: str, data: dict[str, Any]) -> None: ...

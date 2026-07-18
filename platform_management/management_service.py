# ManagementService — orchestrates existing platform services (no business logic).

from __future__ import annotations

import logging
from typing import Any

from platform_management.exceptions import ManagementAPIError, ManagementNotFoundError
from platform_management.management_context import ManagementContext
from platform_management.statistics import (
    get_event_bus_overview,
    get_kpi_dashboard,
    get_request_statistics,
)

logger = logging.getLogger(__name__)

_MANAGEMENT_ACCESS = "MANAGEMENT_API_ACCESS"


class ManagementService:
    # ---- logging ----

    @staticmethod
    async def log_request(
        ctx: ManagementContext,
        *,
        status: int,
        error: str | None = None,
    ) -> None:
        payload = {
            **ctx.log_fields(),
            "status": status,
            "error": error,
        }
        logger.info(
            "management_api_request",
            extra=payload,
        )
        try:
            from platform_legacy import legacy

            audit_id = await legacy.audit.log(
                event_type=_MANAGEMENT_ACCESS,
                entity_type="management_api",
                entity_id=ctx.request_id,
                user_id=ctx.actor_telegram_id,
                payload=payload,
            )
            ctx.audit_id = audit_id
        except Exception:
            logger.debug("management_audit_log_skipped", exc_info=True)

    # ---- system / health ----

    @staticmethod
    async def system_info() -> dict[str, Any]:
        from platform_management.system_info import get_system_info

        return await get_system_info()

    @staticmethod
    async def health() -> dict[str, Any]:
        from platform_management.health import get_health_snapshot

        return await get_health_snapshot()

    # ---- configuration (delegate) ----

    @staticmethod
    async def config_get(key: str, *, actor_telegram_id: int | None = None) -> Any:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.get(
            key,
            actor_telegram_id=actor_telegram_id,
            require_actor=True,
        )

    @staticmethod
    async def config_set(
        key: str,
        value: Any,
        *,
        changed_by: str | None,
        reason: str | None,
        actor_telegram_id: int | None,
    ) -> dict[str, Any]:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.set(
            key,
            value,
            changed_by=changed_by,
            reason=reason,
            actor_telegram_id=actor_telegram_id,
            require_actor=True,
        )

    @staticmethod
    async def config_delete(
        key: str,
        *,
        changed_by: str | None,
        reason: str | None,
        actor_telegram_id: int | None,
    ) -> dict[str, Any] | None:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.delete(
            key,
            changed_by=changed_by,
            reason=reason,
            actor_telegram_id=actor_telegram_id,
            require_actor=True,
        )

    @staticmethod
    async def config_rollback(
        key: str,
        version: int,
        *,
        changed_by: str | None,
        reason: str | None,
        actor_telegram_id: int | None,
    ) -> dict[str, Any] | None:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.rollback(
            key,
            version,
            changed_by=changed_by,
            reason=reason,
            actor_telegram_id=actor_telegram_id,
            require_actor=True,
        )

    @staticmethod
    async def config_validate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.validate(payload)

    @staticmethod
    async def config_export() -> dict[str, Any]:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.export()

    @staticmethod
    async def config_import(
        payload: dict[str, Any],
        *,
        changed_by: str | None,
        reason: str | None,
        actor_telegram_id: int | None,
    ) -> dict[str, Any]:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.import_config(
            payload,
            changed_by=changed_by,
            reason=reason,
            actor_telegram_id=actor_telegram_id,
            require_actor=True,
        )

    @staticmethod
    async def config_list(*, section: str | None = None) -> dict[str, Any]:
        from platform_configuration.config_provider import config_provider
        from platform_configuration.config_schema import ConfigSection

        if section:
            sec = ConfigSection(section)
            return config_provider.get_section(sec)
        return config_provider.snapshot()

    @staticmethod
    async def config_history(key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        from platform_configuration.config_service import configuration_service

        return await configuration_service.get_history(key, limit=limit)

    # ---- verticals ----

    @staticmethod
    async def list_verticals() -> list[dict[str, Any]]:
        from platform_configuration.config_provider import config_provider
        from platform_sdk.vertical_registry import vertical_registry

        items = []
        for entry in vertical_registry.list():
            code = entry["code"]
            detail = await ManagementService.get_vertical(code)
            items.append(detail)
        return items

    @staticmethod
    async def get_vertical(code: str) -> dict[str, Any]:
        from platform_configuration.config_provider import config_provider
        from platform_sdk.base_vertical import SlaPolicy
        from platform_sdk.vertical_registry import vertical_registry

        key = code.strip().lower()
        try:
            cls = vertical_registry.get(key)
        except Exception as exc:
            raise ManagementNotFoundError(f"Vertical not found: {code}") from exc

        entry = next((e for e in vertical_registry.list() if e["code"] == key), {})
        sla = config_provider.sla_settings()
        return {
            **entry,
            **cls.vertical_metadata(),
            "enabled": config_provider.is_vertical_enabled(key),
            "workflow": cls.workflow_name,
            "status": "enabled" if config_provider.is_vertical_enabled(key) else "disabled",
            "manager_strategy": cls.manager_strategy,
            "sla": SlaPolicy(
                assignment_sec=sla["assignment_sec"],
                first_response_sec=sla["first_response_sec"],
                close_sec=sla["close_sec"],
            ).__dict__,
            "version": 1,
        }

    @staticmethod
    async def vertical_enable(code: str, *, actor_telegram_id: int | None) -> dict[str, Any]:
        key = f"feature_flags.verticals.{code.strip().lower()}"
        return await ManagementService.config_set(
            key,
            True,
            changed_by=str(actor_telegram_id) if actor_telegram_id else "management",
            reason="vertical_enable",
            actor_telegram_id=actor_telegram_id,
        )

    @staticmethod
    async def vertical_disable(code: str, *, actor_telegram_id: int | None) -> dict[str, Any]:
        key = f"feature_flags.verticals.{code.strip().lower()}"
        return await ManagementService.config_set(
            key,
            False,
            changed_by=str(actor_telegram_id) if actor_telegram_id else "management",
            reason="vertical_disable",
            actor_telegram_id=actor_telegram_id,
        )

    @staticmethod
    async def vertical_reload(code: str) -> dict[str, Any]:
        from platform_sdk.bootstrap import bootstrap_platform_sdk

        result = await bootstrap_platform_sdk()
        return {"vertical": code.strip().lower(), "bootstrap": result}

    # ---- workflows ----

    @staticmethod
    async def list_workflows() -> dict[str, Any]:
        from workflow.workflow_engine import workflow_engine

        return await workflow_engine.get_statistics()

    @staticmethod
    async def reload_workflows() -> dict[str, Any]:
        from platform_sdk.workflow_loader import sdk_workflow_loader

        count = sdk_workflow_loader.reload()
        return {"reloaded": count}

    @staticmethod
    async def validate_workflows() -> dict[str, Any]:
        from platform_configuration.config_service import configuration_service
        from workflow.workflow_registry import workflow_registry

        definitions = [w.to_dict() for w in workflow_registry.list_all()]
        return {"valid": True, "workflows": len(definitions), "definitions": definitions}

    @staticmethod
    async def workflow_statistics() -> dict[str, Any]:
        from workflow.workflow_engine import workflow_engine

        return await workflow_engine.get_statistics()

    @staticmethod
    async def workflow_executions() -> dict[str, Any]:
        from workflow.workflow_engine import workflow_engine

        stats = await workflow_engine.get_statistics()
        return {
            "active_executions": stats.get("active_executions", 0),
            "statistics": stats,
        }

    # ---- SLA dashboard ----

    @staticmethod
    async def sla_overdue(*, limit: int = 100) -> list:
        from services.sla_dashboard_service import sla_dashboard_service

        return await sla_dashboard_service.get_overdue(limit=limit)

    @staticmethod
    async def sla_at_risk(*, limit: int = 100) -> list:
        from services.sla_dashboard_service import sla_dashboard_service

        return await sla_dashboard_service.get_at_risk(limit=limit)

    @staticmethod
    async def sla_statistics() -> dict[str, Any]:
        from services.sla_dashboard_service import sla_dashboard_service

        return await sla_dashboard_service.get_statistics()

    @staticmethod
    async def sla_owner_escalated(*, limit: int = 100) -> list:
        from services.sla_dashboard_service import sla_dashboard_service

        return await sla_dashboard_service.get_owner_escalated(limit=limit)

    # ---- managers ----

    @staticmethod
    async def managers_overview(*, vertical: str | None = None) -> dict[str, Any]:
        from services.manager_pool_service import manager_pool_service
        from services.smart_assignment_service import smart_assignment_service

        pool = await manager_pool_service.get_pool_dashboard(vertical=vertical)
        assignment = await smart_assignment_service.get_statistics()
        return {
            "pool": pool,
            "assignment_strategy": assignment.get("strategy"),
            "statistics": assignment,
            "current_workload": pool.get("kpi", {}),
            "availability": {
                "busy_managers": pool.get("kpi", {}).get("busy_managers", 0),
                "idle_managers": pool.get("kpi", {}).get("idle_managers", 0),
            },
            "queue_length": pool.get("active_requests", 0),
        }

    # ---- requests ----

    @staticmethod
    async def requests_overview() -> dict[str, Any]:
        return await get_request_statistics()

    # ---- event bus ----

    @staticmethod
    async def event_bus_status() -> dict[str, Any]:
        return await get_event_bus_overview()

    # ---- audit ----

    @staticmethod
    async def audit_search(
        *,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        from audit.audit_service import audit_service

        return await audit_service.search(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )

    @staticmethod
    async def audit_export(
        *,
        event_type: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        rows = await ManagementService.audit_search(event_type=event_type, limit=limit)
        return {"exported": len(rows), "entries": rows}

    @staticmethod
    async def audit_history(
        *,
        request_id: str | None = None,
        manager_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        from audit.audit_service import audit_service

        if request_id:
            return await audit_service.get_request_history(request_id=request_id, limit=limit)
        if manager_id:
            return await audit_service.get_manager_history(manager_id, limit=limit)
        return await ManagementService.audit_search(limit=limit)

    # ---- kpi ----

    @staticmethod
    async def kpi_current(*, period: str = "month") -> dict[str, Any]:
        return await get_kpi_dashboard(period=period)  # type: ignore[arg-type]

    @staticmethod
    async def config_diagnostics() -> dict[str, Any]:
        from platform_configuration.configuration_center import configuration_center

        return {
            "settings": configuration_center.redacted_export(),
            "diagnostics": configuration_center.diagnostics(),
        }

    @staticmethod
    async def config_reload() -> dict[str, Any]:
        from platform_configuration.configuration_center import configuration_center

        configuration_center.reload()
        return configuration_center.diagnostics()

    @staticmethod
    async def legacy_metrics() -> dict[str, Any]:
        from platform_legacy.migration_report import build_migration_report

        return build_migration_report()

    @staticmethod
    async def migration_status() -> dict[str, Any]:
        from platform_legacy.migration_report import build_migration_status

        return build_migration_status()

    @staticmethod
    async def migration_coverage() -> dict[str, Any]:
        from platform_legacy.migration_report import build_coverage_report

        return build_coverage_report()

    @staticmethod
    async def migration_deprecated() -> dict[str, Any]:
        from platform_legacy.deprecation import list_registered_deprecations
        from platform_legacy.deprecation_manager import deprecation_manager

        return {
            "deprecated_apis": deprecation_manager.list_deprecated(),
            "registered_deprecations": list_registered_deprecations(),
        }

    @staticmethod
    async def migration_feature_flags() -> dict[str, Any]:
        from platform_legacy.feature_flags import LEGACY_FLAG_KEYS, load_legacy_migration_flags

        flags = load_legacy_migration_flags()
        return {"flags": flags.to_dict(), "subsystem_map": dict(LEGACY_FLAG_KEYS)}

    @staticmethod
    async def migration_health_report() -> dict[str, Any]:
        from platform_legacy.health import migration_health

        return migration_health()

    # ---- plugins ----

    @staticmethod
    async def plugins_status() -> dict[str, Any]:
        from platform_plugins.plugin_manager import plugin_manager

        return await plugin_manager.list_plugins()

    @staticmethod
    async def plugins_reload() -> dict[str, Any]:
        from platform_plugins.plugin_manager import plugin_manager

        return await plugin_manager.reload()

    # ---- ai (stub) ----

    @staticmethod
    async def ai_providers() -> dict[str, Any]:
        from platform_ai.ai_service import ai_service

        status = await ai_service.status()
        return {"providers": status.get("providers", []), "configured": status.get("providers", [])}

    # ---- feature flags ----

    @staticmethod
    async def feature_flags_list() -> dict[str, Any]:
        from platform_configuration.config_provider import config_provider
        from platform_configuration.config_schema import ConfigSection

        return config_provider.get_section(ConfigSection.FEATURE_FLAGS)

    @staticmethod
    async def feature_flag_enable(key: str, *, actor_telegram_id: int | None) -> dict[str, Any]:
        full_key = key if key.startswith("feature_flags.") else f"feature_flags.{key}"
        return await ManagementService.config_set(
            full_key,
            True,
            changed_by=str(actor_telegram_id) if actor_telegram_id else "management",
            reason="feature_flag_enable",
            actor_telegram_id=actor_telegram_id,
        )

    @staticmethod
    async def feature_flag_disable(key: str, *, actor_telegram_id: int | None) -> dict[str, Any]:
        full_key = key if key.startswith("feature_flags.") else f"feature_flags.{key}"
        return await ManagementService.config_set(
            full_key,
            False,
            changed_by=str(actor_telegram_id) if actor_telegram_id else "management",
            reason="feature_flag_disable",
            actor_telegram_id=actor_telegram_id,
        )

    @staticmethod
    async def feature_flags_validate() -> dict[str, Any]:
        flags = await ManagementService.feature_flags_list()
        return await ManagementService.config_validate(flags)


management_service = ManagementService()

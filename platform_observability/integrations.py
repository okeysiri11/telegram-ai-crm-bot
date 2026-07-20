# Integration bridges — Workflow, Reasoning, Planning, Decision, Learning, Collaboration, Tools, Security, Agents, Orchestrator.

from __future__ import annotations

import logging

from platform_observability.log_manager import log_manager
from platform_observability.metrics_manager import metrics_manager
from platform_observability.models import MonitoringContext
from platform_observability.trace_manager import trace_manager

logger = logging.getLogger(__name__)


class ObservabilityIntegrations:
    @staticmethod
    def context_from_request(
        *,
        request_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
    ) -> MonitoringContext:
        from platform_observability.logging_service import logging_service

        cid = logging_service.new_correlation_id()
        return MonitoringContext(
            correlation_id=cid,
            request_id=request_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
        )

    @staticmethod
    async def trace_workflow_execution(workflow_id: str, name: str) -> str:
        ctx = MonitoringContext(workflow_id=workflow_id, component="workflow")
        trace_id = trace_manager.start_request_trace(name, ctx)
        log_manager.apply_context(ctx)
        log_manager.info(f"Workflow started: {name}", component="workflow", extra={"workflow_id": workflow_id})
        return trace_id

    @staticmethod
    async def record_engine_metrics() -> dict:
        return await metrics_manager.collect_platform_engines()

    @staticmethod
    async def bridge_security_audit(event_type: str, *, principal_id: str | None = None) -> None:
        try:
            from platform_security.audit import audit_manager
            from platform_security.models import AuditEventType

            et = AuditEventType.SECURITY
            if event_type == "authentication":
                et = AuditEventType.AUTHENTICATION
            await audit_manager.log_security_event(event_type, principal_id=principal_id)
        except Exception:
            logger.debug("security audit bridge unavailable")

    @staticmethod
    def orchestrator_context(agent_id: str, capability: str) -> MonitoringContext:
        ctx = ObservabilityIntegrations.context_from_request(agent_id=agent_id)
        ctx.component = "orchestrator"
        ctx.metadata["capability"] = capability
        log_manager.apply_context(ctx)
        return ctx


observability_integrations = ObservabilityIntegrations()

# Integration bridges — Security, Observability, Reliability, Workflow, Tools, Memory, Agents, Orchestrator.

from __future__ import annotations

import logging
from typing import Any

from platform_configuration.models import ConfigurationSnapshot, DeploymentRecord

logger = logging.getLogger(__name__)


class ConfigurationIntegrations:
    @staticmethod
    def encrypt_value(name: str, value: str) -> str:
        try:
            from platform_security.secrets import secret_manager

            record = secret_manager.store(name, value)
            return record.secret_id
        except Exception:
            logger.debug("security layer unavailable for encryption")
            return value

    @staticmethod
    def decrypt_value(secret_id: str) -> str:
        try:
            from platform_security.secrets import secret_manager

            return secret_manager.retrieve(secret_id)
        except Exception:
            logger.debug("security layer unavailable for decryption")
            return secret_id

    @staticmethod
    async def observability_log_load(snapshot: ConfigurationSnapshot, duration_ms: float) -> None:
        try:
            from platform_observability import observability_manager

            observability_manager._logs.info(
                f"Configuration loaded for {snapshot.environment}",
                component="configuration",
                extra={"keys": len(snapshot.values), "duration_ms": duration_ms},
            )
        except Exception:
            logger.debug("observability unavailable")

    @staticmethod
    async def reliability_checkpoint_config(snapshot: ConfigurationSnapshot) -> None:
        try:
            from platform_reliability.checkpoint_manager import checkpoint_manager

            checkpoint_manager.save(
                workflow_id=f"config:{snapshot.environment}",
                snapshot=snapshot.to_dict(),
            )
        except Exception:
            logger.debug("reliability layer unavailable")

    @staticmethod
    async def workflow_apply_config(workflow_id: str, config: dict[str, Any]) -> None:
        try:
            from platform_workflow.workflow_engine import workflow_engine

            workflow_engine.update_context(workflow_id, {"configuration": config})
        except Exception:
            logger.debug("workflow engine unavailable")

    @staticmethod
    def memory_store_profile(environment: str, snapshot: dict[str, Any]) -> None:
        try:
            from platform_memory.context_store import context_store

            context_store.set(f"config:profile:{environment}", snapshot)
        except Exception:
            logger.debug("memory engine unavailable")

    @staticmethod
    def agent_config(agent_id: str) -> dict[str, Any]:
        try:
            from platform_agents.registry import agent_registry

            agent = agent_registry.get(agent_id)
            return agent.metadata() if agent else {}
        except Exception:
            return {}

    @staticmethod
    def orchestrator_status() -> dict[str, Any]:
        try:
            from platform_orchestrator.orchestrator_engine import orchestrator_engine

            return orchestrator_engine.status()
        except Exception:
            return {}

    @staticmethod
    async def record_deployment_metrics(record: DeploymentRecord) -> None:
        try:
            from platform_observability.metrics_collector import metrics_collector

            metrics_collector.record_gauge(
                "deployment.duration_ms",
                record.duration_ms,
                tags={"target": record.target.value, "environment": record.environment},
            )
        except Exception:
            logger.debug("observability metrics unavailable")


configuration_integrations = ConfigurationIntegrations()

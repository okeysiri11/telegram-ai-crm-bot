# IntegrationTestManager — validate platform module integrations via bridges.

from __future__ import annotations

import importlib
import logging
import time
from typing import Any

from platform_validation.models import ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)

_MODULE_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("events", "events", "events.event_bus"),
    ("agent_registry", "platform_agents", "platform_agents.registry"),
    ("memory_engine", "platform_memory", "platform_memory"),
    ("workflow_engine", "platform_workflow", "platform_workflow"),
    ("tool_framework", "platform_tools", "platform_tools"),
    ("security_layer", "platform_security", "platform_security"),
    ("observability_layer", "platform_observability", "platform_observability"),
    ("reliability_layer", "platform_reliability", "platform_reliability"),
    ("configuration_layer", "platform_configuration", "platform_configuration"),
    ("collaboration_layer", "platform_collaboration", "platform_collaboration"),
    ("learning_layer", "platform_learning", "platform_learning"),
    ("orchestrator", "platform_orchestrator", "platform_orchestrator"),
    ("reasoning_engine", "platform_reasoning", "platform_reasoning"),
    ("planning_engine", "platform_planning", "platform_planning"),
    ("decision_engine", "platform_decision", "platform_decision"),
)


class IntegrationTestManager:
    """Validates all platform modules and integration bridges."""

    def __init__(self) -> None:
        self._custom_checks: list[tuple[str, str, Any]] = []

    def reset(self) -> None:
        self._custom_checks.clear()

    def register_check(self, check_id: str, component: str, fn: Any) -> None:
        self._custom_checks.append((check_id, component, fn))

    def _import_module(self, module_path: str) -> bool:
        try:
            importlib.import_module(module_path)
            return True
        except Exception as exc:
            logger.debug("module_import_failed path=%s error=%s", module_path, exc)
            return False

    def _run_bridge_check(self, component: str) -> ValidationCheck:
        started = time.perf_counter()
        ok = False
        message = "bridge unavailable"
        try:
            if component == "events":
                from events.event_bus import PlatformEventBus

                ok = PlatformEventBus is not None
                message = "Event bus available"
            elif component == "agent_registry":
                from platform_agents.registry import agent_registry

                ok = agent_registry.list_agents() is not None
                message = f"Agent registry: {len(agent_registry.list_agents())} agents"
            elif component == "memory_engine":
                from platform_memory import memory_service

                ok = memory_service is not None
                message = "Memory engine available"
            elif component == "workflow_engine":
                from platform_workflow import workflow_engine

                ok = workflow_engine is not None
                message = "Workflow engine available"
            elif component == "tool_framework":
                from platform_tools import tool_registry

                ok = tool_registry is not None
                message = "Tool framework available"
            elif component == "security_layer":
                from platform_security import security_manager

                ok = security_manager is not None
                message = "Security layer available"
            elif component == "observability_layer":
                from platform_observability import observability_manager

                ok = observability_manager is not None
                message = "Observability layer available"
            elif component == "reliability_layer":
                from platform_reliability import reliability_manager

                ok = reliability_manager is not None
                message = "Reliability layer available"
            elif component == "configuration_layer":
                from platform_configuration import configuration_manager

                ok = configuration_manager is not None
                message = "Configuration layer available"
            elif component == "collaboration_layer":
                from platform_collaboration import collaboration_engine

                ok = collaboration_engine is not None
                message = "Collaboration engine available"
            elif component == "learning_layer":
                from platform_learning import learning_engine

                ok = learning_engine is not None
                message = "Learning engine available"
            elif component == "orchestrator":
                from platform_orchestrator import platform_orchestrator

                ok = platform_orchestrator is not None
                message = "Orchestrator available"
            elif component == "reasoning_engine":
                from platform_reasoning import reasoning_engine

                ok = reasoning_engine is not None
                message = "Reasoning engine available"
            elif component == "planning_engine":
                from platform_planning import planning_engine

                ok = planning_engine is not None
                message = "Planning engine available"
            elif component == "decision_engine":
                from platform_decision import decision_engine

                ok = decision_engine is not None
                message = "Decision engine available"
            else:
                message = f"No bridge for {component}"
        except Exception as exc:
            message = str(exc)

        duration_ms = (time.perf_counter() - started) * 1000.0
        return ValidationCheck(
            check_id=f"integration.{component}",
            component=component,
            status=ValidationStatus.PASS if ok else ValidationStatus.FAIL,
            message=message,
            duration_ms=duration_ms,
        )

    async def validate_all(self) -> ValidationReport:
        report = ValidationReport(title="Integration Validation Report")
        for check_id, component, module_path in _MODULE_CHECKS:
            started = time.perf_counter()
            imported = self._import_module(module_path)
            duration_ms = (time.perf_counter() - started) * 1000.0
            report.checks.append(
                ValidationCheck(
                    check_id=f"module.{check_id}",
                    component=component,
                    status=ValidationStatus.PASS if imported else ValidationStatus.FAIL,
                    message=f"Module {module_path} {'loaded' if imported else 'failed'}",
                    duration_ms=duration_ms,
                )
            )
            if imported:
                report.checks.append(self._run_bridge_check(check_id))

        for check_id, component, fn in self._custom_checks:
            started = time.perf_counter()
            try:
                result = fn()
                if hasattr(result, "__await__"):
                    result = await result
                ok = bool(result)
                message = "custom check passed" if ok else "custom check failed"
                status = ValidationStatus.PASS if ok else ValidationStatus.FAIL
            except Exception as exc:
                ok = False
                message = str(exc)
                status = ValidationStatus.FAIL
            report.checks.append(
                ValidationCheck(
                    check_id=check_id,
                    component=component,
                    status=status,
                    message=message,
                    duration_ms=(time.perf_counter() - started) * 1000.0,
                )
            )

        return report.finalize()


integration_test_manager = IntegrationTestManager()

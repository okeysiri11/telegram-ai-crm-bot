"""Tests — unified Workflow Engine."""

from __future__ import annotations

import pytest

from platform_workflows.models import StepType, WorkflowExecutionRequest
from platform_workflows.workflow_engine import workflow_engine
from platform_workflows.workflow_loader import parse_workflow_document
from platform_workflows.workflow_registry import WorkflowRegistry
from platform_workflows.workflow_validator import WorkflowValidator


@pytest.fixture(autouse=True)
def _reset_engine():
    workflow_engine.reset()
    yield
    workflow_engine.reset()


def test_single_engine_yaml_and_python():
    workflow_engine.initialize()
    ids = set(workflow_engine.registry.list_ids())
    assert "agro_post_create" in ids or "realty_post_create" in ids
    assert "vehicle_intake" in ids


def test_architecture_layers_exist():
    from platform_workflows import workflow_registry, workflow_executor, workflow_steps
    from platform_workflows import services

    assert workflow_registry is not None
    assert workflow_executor is not None
    assert workflow_steps is not None
    assert services.list_services()


def test_yaml_definition_parsing():
    data = {
        "workflow": {
            "id": "test_flow",
            "vertical": "AUTO",
            "steps": [
                {"id": "notify", "type": "service", "service": "NotificationService", "method": "notify"},
                {"id": "done", "type": "complete"},
            ],
        }
    }
    definition = parse_workflow_document(data)
    errors = WorkflowValidator.validate(definition)
    assert not errors


@pytest.mark.asyncio
async def test_legacy_rule_adapter_delegates():
    from platform_workflows.adapters.legacy_rules import LegacyRuleEngineAdapter

    assert LegacyRuleEngineAdapter is not None
    assert hasattr(LegacyRuleEngineAdapter, "execute_workflow")


@pytest.mark.asyncio
async def test_ai_execution_via_unified_engine():
    from platform_ai.ai_service import ai_service

    ai_service.initialize()
    workflow_engine.initialize()
    result = await workflow_engine.execute(
        WorkflowExecutionRequest(
            workflow_id="insurance_quote",
            input={"profile": {"age": 35}},
            plugin_id="insurance",
        )
    )
    assert result.status == "completed"
    assert result.workflow_id == "insurance_quote"


def test_no_duplicate_runtime_modules():
    from platform_workflows import workflow_executor as unified_executor
    from workflow.workflow_executor import workflow_executor as legacy_executor
    from platform_ai.workflows.workflow_executor import workflow_executor as ai_executor

    assert legacy_executor is unified_executor
    assert ai_executor is unified_executor

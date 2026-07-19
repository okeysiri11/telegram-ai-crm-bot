# Python workflow definitions — AI templates registered into the unified engine.

from __future__ import annotations

from platform_workflows.models import StepDefinition, StepType, WorkflowDefinition
from platform_workflows.workflow_registry import WorkflowRegistry


def _convert_ai_workflow(old_def: Any) -> WorkflowDefinition:
    steps: dict[str, StepDefinition] = {}
    for sid, step in old_def.steps.items():
        steps[sid] = StepDefinition.from_dict(step.to_dict(), step_id=sid)
    return WorkflowDefinition(
        id=old_def.workflow_id,
        vertical=str(getattr(old_def, "category", "AI")).upper(),
        description=getattr(old_def, "description", "") or getattr(old_def, "name", ""),
        steps=steps,
        entry_step=old_def.entry_step,
        version=getattr(old_def, "version", "1.0.0"),
        category=getattr(old_def, "category", "general"),
        tags=list(getattr(old_def, "tags", [])),
        enabled=getattr(old_def, "enabled", True),
        metadata={"name": getattr(old_def, "name", old_def.workflow_id)},
    )


def _vehicle_intake_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="vehicle_intake",
        vertical="AUTO",
        description="Decode VIN, generate description, and estimate price.",
        category="auto",
        tags=["auto", "intake", "pipeline"],
        entry_step="decode_vin",
        steps={
            "decode_vin": StepDefinition(
                id="decode_vin",
                type=StepType.SKILL,
                config={
                    "skill_id": "vin_decoder",
                    "input_mapping": {"vin": "$input.vin"},
                    "output_key": "vehicle",
                },
                next_step="describe",
            ),
            "describe": StepDefinition(
                id="describe",
                type=StepType.SKILL,
                config={
                    "skill_id": "vehicle_description",
                    "input_mapping": {"vehicle_specs": "$memory.vehicle"},
                    "output_key": "description",
                },
                next_step="estimate_price",
            ),
            "estimate_price": StepDefinition(
                id="estimate_price",
                type=StepType.SKILL,
                config={
                    "skill_id": "price_estimation",
                    "input_mapping": {"item_description": "$memory.description.result"},
                    "output_key": "pricing",
                },
                next_step="finalize",
            ),
            "finalize": StepDefinition(
                id="finalize",
                type=StepType.TRANSFORM,
                config={
                    "mapping": {
                        "vehicle": "$memory.vehicle",
                        "description": "$memory.description",
                        "pricing": "$memory.pricing",
                    },
                    "output_key": "final",
                },
                next_step="end",
            ),
        },
    )


def _lead_qualification_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="lead_qualification",
        vertical="CRM",
        description="Detect intent, score lead, assess risk.",
        category="sales",
        tags=["sales", "leads", "qualification"],
        entry_step="detect_intent",
        steps={
            "detect_intent": StepDefinition(
                id="detect_intent",
                type=StepType.SKILL,
                config={
                    "skill_id": "intent_detection",
                    "input_mapping": {"message": "$input.message"},
                    "output_key": "intent",
                },
                next_step="score_lead",
            ),
            "score_lead": StepDefinition(
                id="score_lead",
                type=StepType.SKILL,
                config={
                    "skill_id": "lead_scoring",
                    "input_mapping": {
                        "lead_profile": "$input.lead_profile",
                        "lead_data": "$memory.intent",
                    },
                    "output_key": "score",
                },
                next_step="assess_risk",
            ),
            "assess_risk": StepDefinition(
                id="assess_risk",
                type=StepType.SKILL,
                config={
                    "skill_id": "risk_assessment",
                    "input_mapping": {
                        "scenario": "$input.message",
                        "profile": "$memory.score",
                    },
                    "output_key": "risk",
                },
                next_step="finalize",
            ),
            "finalize": StepDefinition(
                id="finalize",
                type=StepType.TRANSFORM,
                config={
                    "mapping": {
                        "intent": "$memory.intent",
                        "score": "$memory.score",
                        "risk": "$memory.risk",
                    },
                    "output_key": "final",
                },
                next_step="end",
            ),
        },
    )


def _document_analysis_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="document_analysis",
        vertical="LEGAL",
        description="Summarize document and analyze contract in parallel.",
        category="legal",
        tags=["documents", "legal", "parallel"],
        entry_step="summarize",
        steps={
            "summarize": StepDefinition(
                id="summarize",
                type=StepType.SKILL,
                config={
                    "skill_id": "document_summary",
                    "input_mapping": {"text": "$input.text"},
                    "output_key": "summary",
                },
                next_step="parallel_analysis",
            ),
            "parallel_analysis": StepDefinition(
                id="parallel_analysis",
                type=StepType.PARALLEL,
                branches=["contract_check", "risk_check"],
                config={"output_key": "parallel_results"},
                next_step="merge_all",
            ),
            "contract_check": StepDefinition(
                id="contract_check",
                type=StepType.SKILL,
                config={
                    "skill_id": "contract_analysis",
                    "input_mapping": {"contract_text": "$input.text"},
                    "output_key": "contract",
                },
                retries=1,
                timeout_seconds=30.0,
            ),
            "risk_check": StepDefinition(
                id="risk_check",
                type=StepType.SKILL,
                config={
                    "skill_id": "risk_assessment",
                    "input_mapping": {"scenario": "$memory.summary.result"},
                    "output_key": "risk",
                },
                fallback="summary_only",
            ),
            "summary_only": StepDefinition(
                id="summary_only",
                type=StepType.TRANSFORM,
                config={"mapping": {"summary": "$memory.summary"}, "output_key": "risk"},
            ),
            "merge_all": StepDefinition(
                id="merge_all",
                type=StepType.MERGE,
                config={"keys": ["summary", "contract", "risk"], "output_key": "final"},
                next_step="end",
            ),
        },
    )


def _insurance_quote_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="insurance_quote",
        vertical="INSURANCE",
        description="Recommend insurance products based on profile.",
        category="insurance",
        tags=["insurance", "recommendation"],
        entry_step="recommend",
        steps={
            "recommend": StepDefinition(
                id="recommend",
                type=StepType.SKILL,
                config={
                    "skill_id": "insurance_recommendation",
                    "input_mapping": {"profile": "$input.profile"},
                    "output_key": "recommendations",
                },
                next_step="finalize",
            ),
            "finalize": StepDefinition(
                id="finalize",
                type=StepType.TRANSFORM,
                config={"mapping": {"recommendations": "$memory.recommendations"}, "output_key": "final"},
                next_step="end",
            ),
        },
    )


_TEMPLATES = [
    _vehicle_intake_workflow,
    _lead_qualification_workflow,
    _document_analysis_workflow,
    _insurance_quote_workflow,
]


def register_builtin_workflows(registry: WorkflowRegistry) -> int:
    count = 0
    for factory in _TEMPLATES:
        registry.register(factory(), source="python")
        count += 1
    return count


def list_template_metadata() -> list[dict]:
    return [factory().to_dict() for factory in _TEMPLATES]


from typing import Any  # noqa: E402

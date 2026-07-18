# Built-in AI workflow templates — reusable cognitive pipelines.

from __future__ import annotations

from platform_ai.workflows.models import StepType, WorkflowDefinition, WorkflowStep
from platform_ai.workflows.workflow_registry import workflow_registry


def _vehicle_intake_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="vehicle_intake",
        name="Vehicle Intake Pipeline",
        description="Decode VIN, generate description, and estimate price.",
        category="auto",
        tags=["auto", "intake", "pipeline"],
        entry_step="decode_vin",
        steps={
            "decode_vin": WorkflowStep(
                step_id="decode_vin",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "vin_decoder",
                    "input_mapping": {"vin": "$input.vin"},
                    "output_key": "vehicle",
                },
                next="describe",
            ),
            "describe": WorkflowStep(
                step_id="describe",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "vehicle_description",
                    "input_mapping": {"vehicle_specs": "$memory.vehicle"},
                    "output_key": "description",
                },
                next="estimate_price",
            ),
            "estimate_price": WorkflowStep(
                step_id="estimate_price",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "price_estimation",
                    "input_mapping": {"item_description": "$memory.description.result"},
                    "output_key": "pricing",
                },
                next="finalize",
            ),
            "finalize": WorkflowStep(
                step_id="finalize",
                step_type=StepType.TRANSFORM.value,
                config={
                    "mapping": {
                        "vehicle": "$memory.vehicle",
                        "description": "$memory.description",
                        "pricing": "$memory.pricing",
                    },
                    "output_key": "final",
                },
                next="end",
            ),
        },
    )


def _lead_qualification_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="lead_qualification",
        name="Lead Qualification Pipeline",
        description="Detect intent, score lead, assess risk.",
        category="sales",
        tags=["sales", "leads", "qualification"],
        entry_step="detect_intent",
        steps={
            "detect_intent": WorkflowStep(
                step_id="detect_intent",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "intent_detection",
                    "input_mapping": {"message": "$input.message"},
                    "output_key": "intent",
                },
                next="check_intent",
            ),
            "check_intent": WorkflowStep(
                step_id="check_intent",
                step_type=StepType.CONDITION.value,
                config={"expression": "$memory.intent.intent"},
                on_true="score_lead",
                on_false="low_priority",
            ),
            "score_lead": WorkflowStep(
                step_id="score_lead",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "lead_scoring",
                    "input_mapping": {"lead_profile": "$input.lead_profile"},
                    "output_key": "score",
                },
                next="assess_risk",
                retries=1,
            ),
            "assess_risk": WorkflowStep(
                step_id="assess_risk",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "risk_assessment",
                    "input_mapping": {"scenario": "$input.lead_profile"},
                    "output_key": "risk",
                },
                next="merge_results",
            ),
            "low_priority": WorkflowStep(
                step_id="low_priority",
                step_type=StepType.TRANSFORM.value,
                config={
                    "mapping": {"priority": "low", "intent": "$memory.intent"},
                    "output_key": "final",
                },
                next="end",
            ),
            "merge_results": WorkflowStep(
                step_id="merge_results",
                step_type=StepType.MERGE.value,
                config={"keys": ["intent", "score", "risk"], "output_key": "final"},
                next="end",
            ),
        },
    )


def _document_analysis_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="document_analysis",
        name="Document Analysis Pipeline",
        description="Summarize document and analyze contract in parallel.",
        category="legal",
        tags=["documents", "legal", "parallel"],
        entry_step="summarize",
        steps={
            "summarize": WorkflowStep(
                step_id="summarize",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "document_summary",
                    "input_mapping": {"text": "$input.text"},
                    "output_key": "summary",
                },
                next="parallel_analysis",
            ),
            "parallel_analysis": WorkflowStep(
                step_id="parallel_analysis",
                step_type=StepType.PARALLEL.value,
                branches=["contract_check", "risk_check"],
                config={"output_key": "parallel_results"},
                next="merge_all",
            ),
            "contract_check": WorkflowStep(
                step_id="contract_check",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "contract_analysis",
                    "input_mapping": {"contract_text": "$input.text"},
                    "output_key": "contract",
                },
                retries=1,
                timeout_seconds=30.0,
            ),
            "risk_check": WorkflowStep(
                step_id="risk_check",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "risk_assessment",
                    "input_mapping": {"scenario": "$memory.summary.result"},
                    "output_key": "risk",
                },
                fallback="summary_only",
            ),
            "summary_only": WorkflowStep(
                step_id="summary_only",
                step_type=StepType.TRANSFORM.value,
                config={"mapping": {"summary": "$memory.summary"}, "output_key": "risk"},
            ),
            "merge_all": WorkflowStep(
                step_id="merge_all",
                step_type=StepType.MERGE.value,
                config={"keys": ["summary", "contract", "risk"], "output_key": "final"},
                next="end",
            ),
        },
    )


def _insurance_quote_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="insurance_quote",
        name="Insurance Quote Pipeline",
        description="Recommend insurance products based on profile.",
        category="insurance",
        tags=["insurance", "recommendation"],
        entry_step="recommend",
        steps={
            "recommend": WorkflowStep(
                step_id="recommend",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "insurance_recommendation",
                    "input_mapping": {"profile": "$input.profile"},
                    "output_key": "recommendations",
                },
                next="finalize",
            ),
            "finalize": WorkflowStep(
                step_id="finalize",
                step_type=StepType.TRANSFORM.value,
                config={"mapping": {"recommendations": "$memory.recommendations"}, "output_key": "final"},
                next="end",
            ),
        },
    )


_TEMPLATES = [
    _vehicle_intake_workflow,
    _lead_qualification_workflow,
    _document_analysis_workflow,
    _insurance_quote_workflow,
]


def register_all() -> None:
    for factory in _TEMPLATES:
        workflow_registry.register(factory())


def list_templates() -> list[dict]:
    return [factory().to_dict() for factory in _TEMPLATES]

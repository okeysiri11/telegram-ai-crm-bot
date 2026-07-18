# WorkflowValidator — structural validation for unified workflow definitions.

from __future__ import annotations

from platform_workflows.exceptions import WorkflowValidationError
from platform_workflows.models import StepDefinition, StepType, WorkflowDefinition


class WorkflowValidator:
    @staticmethod
    def validate(definition: WorkflowDefinition) -> list[str]:
        errors: list[str] = []
        if not definition.id:
            errors.append("workflow id is required")
        if not definition.vertical:
            errors.append("workflow vertical is required")
        if not definition.steps:
            errors.append("workflow must contain steps")

        step_ids = set(definition.steps.keys())
        if len(step_ids) != len(definition.steps):
            errors.append("duplicate step ids detected")

        for step in definition.steps.values():
            errors.extend(WorkflowValidator._validate_step(step, step_ids))

        if definition.entry_step and definition.entry_step not in step_ids:
            errors.append(f"unknown entry_step: {definition.entry_step}")

        complete_steps = [s for s in definition.steps.values() if s.type == StepType.COMPLETE]
        end_terminal = any(s.next_step == "end" for s in definition.steps.values())
        if not complete_steps and not end_terminal:
            errors.append("workflow must include at least one complete step")

        return errors

    @staticmethod
    def _validate_step(step: StepDefinition, known_ids: set[str]) -> list[str]:
        errors: list[str] = []

        if step.type == StepType.SERVICE:
            if not step.config.get("service"):
                errors.append(f"step {step.id}: service step requires service name")
            if not step.config.get("method"):
                errors.append(f"step {step.id}: service step requires method name")

        if step.type == StepType.EVENT and not step.config.get("event_type"):
            errors.append(f"step {step.id}: event step requires event_type")

        if step.type == StepType.CONDITION:
            expr = step.config.get("when") or step.config.get("expression")
            if not expr:
                errors.append(f"step {step.id}: condition step requires when/expression")
            for branch in (step.on_true, step.on_false, step.config.get("then"), step.config.get("else")):
                if branch and str(branch) not in known_ids and str(branch) != "end":
                    errors.append(f"step {step.id}: unknown branch target {branch}")

        if step.type in {StepType.SKILL, StepType.AI}:
            if not (step.config.get("skill_id") or step.config.get("skill")):
                errors.append(f"step {step.id}: skill step requires skill_id")

        if step.type == StepType.CHOICE:
            if not step.config.get("variable"):
                errors.append(f"step {step.id}: choice step requires variable")
            options = step.config.get("options") or {}
            if not isinstance(options, dict) or not options:
                errors.append(f"step {step.id}: choice step requires options map")

        for ref in (step.next_step, step.on_true, step.on_false, step.fallback, *step.branches):
            if ref and str(ref) not in known_ids and str(ref) != "end":
                errors.append(f"step {step.id}: unknown reference {ref}")

        return errors

    @staticmethod
    def validate_or_raise(definition: WorkflowDefinition) -> None:
        errors = WorkflowValidator.validate(definition)
        if errors:
            raise WorkflowValidationError("; ".join(errors))

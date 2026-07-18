# WorkflowValidator — structural validation for workflow definitions.

from __future__ import annotations

from workflow.models import StepDefinition, StepType, WorkflowDefinition


class WorkflowValidationError(ValueError):
    pass


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

        step_ids = [s.id for s in definition.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("duplicate step ids detected")

        known = set(step_ids)
        for step in definition.steps:
            errors.extend(WorkflowValidator._validate_step(step, known))

        complete_steps = [s for s in definition.steps if s.type == StepType.COMPLETE]
        if not complete_steps:
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

        if step.type == StepType.EVENT:
            if not step.config.get("event_type"):
                errors.append(f"step {step.id}: event step requires event_type")

        if step.type == StepType.CONDITION:
            if not step.config.get("when"):
                errors.append(f"step {step.id}: condition step requires when expression")
            for branch in ("then", "else"):
                target = step.config.get(branch)
                if target and str(target) not in known_ids:
                    errors.append(f"step {step.id}: unknown branch target {branch}={target}")

        if step.type == StepType.CHOICE:
            if not step.config.get("variable"):
                errors.append(f"step {step.id}: choice step requires variable")
            options = step.config.get("options") or {}
            if not isinstance(options, dict) or not options:
                errors.append(f"step {step.id}: choice step requires options map")

        if step.next_step and step.next_step not in known_ids:
            errors.append(f"step {step.id}: unknown next_step {step.next_step}")

        return errors

    @staticmethod
    def validate_or_raise(definition: WorkflowDefinition) -> None:
        errors = WorkflowValidator.validate(definition)
        if errors:
            raise WorkflowValidationError("; ".join(errors))

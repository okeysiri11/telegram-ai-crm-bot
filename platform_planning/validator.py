# PlanValidator — circular deps, capabilities, permissions, resources.

from __future__ import annotations

from platform_planning.exceptions import PlanValidationError
from platform_planning.models import ExecutionPlan, PlanningContext, PlanStep


class PlanValidator:
    def validate(self, plan: ExecutionPlan, context: PlanningContext) -> list[str]:
        errors: list[str] = []
        errors.extend(self._check_circular_dependencies(plan.steps))
        errors.extend(self._check_missing_capabilities(plan.steps, context))
        errors.extend(self._check_permissions(plan.steps, context))
        errors.extend(self._check_resources(plan.steps, context))
        if errors:
            raise PlanValidationError("Plan validation failed", details=errors)
        return errors

    def validate_soft(self, plan: ExecutionPlan, context: PlanningContext) -> list[str]:
        try:
            return self.validate(plan, context)
        except PlanValidationError as exc:
            return list(exc.details)

    def _check_circular_dependencies(self, steps: list[PlanStep]) -> list[str]:
        errors: list[str] = []
        step_ids = {s.step_id for s in steps}
        graph = {s.step_id: [d for d in s.depends_on if d in step_ids] for s in steps}

        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for dep in graph.get(node, []):
                if dfs(dep):
                    return True
            stack.discard(node)
            return False

        for step_id in step_ids:
            if dfs(step_id):
                errors.append(f"circular_dependency: cycle detected involving '{step_id}'")
                break
        return errors

    def _check_missing_capabilities(self, steps: list[PlanStep], context: PlanningContext) -> list[str]:
        errors: list[str] = []
        available = set(context.capabilities)
        for step in steps:
            if step.capability and step.capability not in available and available:
                errors.append(f"missing_capability: step '{step.step_id}' requires '{step.capability}'")
        return errors

    def _check_permissions(self, steps: list[PlanStep], context: PlanningContext) -> list[str]:
        errors: list[str] = []
        if not context.permissions:
            return errors
        if "execute" not in context.permissions and "admin" not in context.permissions:
            errors.append("permission_denied: 'execute' permission required")
        return errors

    def _check_resources(self, steps: list[PlanStep], context: PlanningContext) -> list[str]:
        errors: list[str] = []
        available_tools = set(context.available_tools)
        for step in steps:
            if step.tool_id and available_tools and step.tool_id not in available_tools:
                errors.append(f"missing_tool: step '{step.step_id}' requires tool '{step.tool_id}'")
            if step.agent_id and context.available_agents and step.agent_id not in context.available_agents:
                errors.append(f"missing_agent: step '{step.step_id}' requires agent '{step.agent_id}'")
        return errors


plan_validator = PlanValidator()

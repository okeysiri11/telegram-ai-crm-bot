"""Variable / field condition helpers."""

from applications.enterprise_hub.workflow.conditions import evaluate_condition


def check_variable(*, field: str, context: dict | None = None) -> bool:
    return evaluate_condition(
        condition_type="field", expected=field, actual=None, context=context
    )

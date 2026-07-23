"""User condition helpers."""

from applications.enterprise_hub.workflow.conditions import evaluate_condition


def check_user(*, expected: str, actual: str = "", context: dict | None = None) -> bool:
    return evaluate_condition(
        condition_type="user", expected=expected, actual=actual, context=context
    )

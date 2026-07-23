"""AI decision condition helpers."""

from applications.enterprise_hub.workflow.conditions import evaluate_condition


def check_ai(*, expected: str = "approve", actual: str = "", context: dict | None = None) -> bool:
    return evaluate_condition(
        condition_type="ai_decision", expected=expected, actual=actual, context=context
    )

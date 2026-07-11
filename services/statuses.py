# Unified status model for CRM, tasks, workflows and platform entities.

UNIFIED_STATUSES = (
    "NEW",
    "IN_PROGRESS",
    "BLOCKED",
    "DONE",
    "CANCELLED",
    "ARCHIVED",
)

# Legacy CRM / module values → unified status
LEGACY_STATUS_MAP = {
    "COMPLETED": "DONE",
    "COMPLETE": "DONE",
    "CANCELED": "CANCELLED",
    "CANCEL": "CANCELLED",
    "ACTIVE": "IN_PROGRESS",
    "PAUSED": "BLOCKED",
    "FULFILLED": "DONE",
    "DRAFT": "NEW",
    "SIGNED": "IN_PROGRESS",
    "todo": "NEW",
    "done": "DONE",
    "active": "IN_PROGRESS",
}

TERMINAL_STATUSES = frozenset({"DONE", "CANCELLED", "ARCHIVED"})
ACTIVE_STATUSES = frozenset({"NEW", "IN_PROGRESS", "BLOCKED"})


def normalize_status(status: str, default: str = "NEW") -> str:
    if not status:
        return default
    value = str(status).strip().upper()
    value = LEGACY_STATUS_MAP.get(value, value)
    if value in UNIFIED_STATUSES:
        return value
    return default


def is_terminal_status(status: str) -> bool:
    return normalize_status(status) in TERMINAL_STATUSES


def is_active_status(status: str) -> bool:
    return normalize_status(status) in ACTIVE_STATUSES

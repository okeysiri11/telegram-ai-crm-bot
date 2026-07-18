# Event and audit timelines — filterable views over audit trail.

from __future__ import annotations

from typing import Any

_AUDIT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "configuration": ("CONFIGURATION_CHANGED",),
    "permissions": ("MANAGEMENT_API_ACCESS", "PERMISSION_CHANGED"),
    "workflow": ("WORKFLOW_STARTED", "WORKFLOW_COMPLETED", "WORKFLOW_STEP_COMPLETED"),
    "assignments": ("REQUEST_ASSIGNED", "MANAGER_REASSIGNED", "SmartAssignmentCompletedEvent"),
    "plugins": ("PLUGIN_",),
}


async def event_timeline(
    *,
    event_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    from platform_management.management_service import management_service

    rows = await management_service.audit_search(event_type=event_type, limit=limit)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        etype = str(row.get("event_type") or "UNKNOWN")
        grouped.setdefault(etype, []).append(row)

    return {
        "filter": {"event_type": event_type},
        "entries": rows,
        "count": len(rows),
        "grouped_by_type": grouped,
    }


async def audit_timeline(
    *,
    category: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    from platform_management.management_service import management_service

    if category and category in _AUDIT_CATEGORIES:
        prefixes = _AUDIT_CATEGORIES[category]
        rows = await management_service.audit_search(limit=limit * 2)
        filtered = [
            row
            for row in rows
            if any(str(row.get("event_type", "")).startswith(p) for p in prefixes)
        ][:limit]
    else:
        filtered = await management_service.audit_search(limit=limit)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in filtered:
        cat = _categorize_audit(row.get("event_type"))
        grouped.setdefault(cat, []).append(row)

    return {
        "filter": {"category": category},
        "entries": filtered,
        "count": len(filtered),
        "grouped_by_category": grouped,
    }


def _categorize_audit(event_type: Any) -> str:
    et = str(event_type or "")
    for category, prefixes in _AUDIT_CATEGORIES.items():
        if any(et.startswith(p) for p in prefixes):
            return category
    if "REQUEST" in et:
        return "assignments"
    return "other"

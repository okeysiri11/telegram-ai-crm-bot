# Built-in demonstration tools — no external dependencies.

from __future__ import annotations

from typing import Any

from platform_tools.models import ToolCategory, ToolContext, ToolPermission
from platform_tools.registry import ToolRegistry


async def _echo_handler(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload, "agent_id": ctx.agent_id}


async def _http_get_stub(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    url = payload.get("url", "")
    return {"status": 200, "url": url, "body_preview": "(stub — no network call)"}


async def _crm_lookup_stub(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    return {"found": True, "entity_id": payload.get("entity_id", "unknown"), "source": "crm_stub"}


async def _telegram_notify_stub(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "sent": True,
        "chat_id": payload.get("chat_id"),
        "message": payload.get("message", ""),
        "stub": True,
    }


async def _search_stub(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query", "")
    return {"results": [{"title": f"Result for: {query}", "score": 0.95}], "count": 1}


async def _calendar_stub(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    return {"event_id": "evt_stub_001", "title": payload.get("title", "Meeting"), "scheduled": True}


BUILTIN_TOOL_DEFS = [
    ("internal_echo", "Internal Echo", "Echo payload for testing", ToolCategory.INTERNAL, _echo_handler, [ToolPermission.EXECUTE]),
    ("http_get", "HTTP GET", "HTTP GET request (stub)", ToolCategory.HTTP, _http_get_stub, [ToolPermission.READ]),
    ("rest_api_call", "REST API Call", "Generic REST API call (stub)", ToolCategory.REST_API, _http_get_stub, [ToolPermission.READ]),
    ("crm_lookup", "CRM Lookup", "Look up CRM entity (stub)", ToolCategory.CRM, _crm_lookup_stub, [ToolPermission.READ]),
    ("telegram_notify", "Telegram Notify", "Send Telegram notification (stub)", ToolCategory.TELEGRAM, _telegram_notify_stub, [ToolPermission.WRITE]),
    ("search_query", "Search Query", "Search platform data (stub)", ToolCategory.SEARCH, _search_stub, [ToolPermission.READ]),
    ("calendar_create", "Calendar Create", "Create calendar event (stub)", ToolCategory.CALENDAR, _calendar_stub, [ToolPermission.WRITE]),
]


def register_builtin_tools(registry: ToolRegistry) -> list[str]:
    registered: list[str] = []
    for tool_id, name, desc, category, handler, perms in BUILTIN_TOOL_DEFS:
        registry.register_handler(tool_id, name, desc, category, handler, required_permissions=perms)
        registered.append(tool_id)
    return registered


__all__ = ["BUILTIN_TOOL_DEFS", "register_builtin_tools"]

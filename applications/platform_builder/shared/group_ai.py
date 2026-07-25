"""Shared Group AI + team owner action constants — Sprint 28.3."""

from __future__ import annotations

from typing import Any

GROUP_AI_INVITE_ROLES = (
    "Lawyer",
    "Accountant",
    "Marketing",
    "HR",
    "Medical",
    "Finance",
    "Analytics",
    "Custom Specialists",
)

GROUP_AI_CHAT_FOUNDATION: dict[str, Any] = {
    "status": "operational",
    "description": "Owner can start a conversation and invite specialists to discuss together.",
    "invite_roles": list(GROUP_AI_INVITE_ROLES),
    "model": {
        "conversation_id": "string",
        "owner_id": "string",
        "participant_list": ["specialist_id"],
        "speaking_order": ["specialist_id"],
        "conversation_history": [{"role": "string", "text": "string"}],
        "ai_summary": "string",
        "decision_summary": "string",
    },
    "apis": [
        "POST /collaborative-ai/sessions",
        "POST /collaborative-ai/teams/{id}/sessions",
        "GET /collaborative-ai/sessions/{id}/workspace",
        "POST /collaborative-ai/sessions/{id}/tasks",
        "POST /collaborative-ai/sessions/{id}/knowledge",
        "POST /collaborative-ai/sessions/{id}/decide",
        "GET /collaborative-ai/sessions/{id}/summary-report",
    ],
    "runtime": "applications/platform_builder/collaborative_ai",
    "note": "Collaborative AI Engine runtime — Sprint 28.8 Collective Intelligence.",
}

TEAM_OWNER_ACTIONS = (
    "open_chat",
    "assign_task",
    "view_knowledge",
    "view_memory",
    "pause_agent",
    "resume_agent",
    "edit_agent",
    "replace_agent",
    "remove_agent",
)

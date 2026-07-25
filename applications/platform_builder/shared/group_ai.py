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
    "status": "architecture_only",
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
    "apis_planned": [
        "POST /group-ai-chat/sessions",
        "POST /group-ai-chat/sessions/{id}/invite",
        "GET /group-ai-chat/sessions/{id}/history",
        "POST /group-ai-chat/sessions/{id}/summarize",
    ],
    "note": "No live collaborative chat runtime in this sprint — architecture only.",
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

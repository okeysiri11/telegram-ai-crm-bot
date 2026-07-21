# Prompt templates for the unified assistant.

from __future__ import annotations

from typing import Any


SYSTEM_PROMPTS = {
    "default": (
        "You are the Unified AI Assistant for the AI Ecosystem. "
        "You operate across applications, use skills, and maintain global knowledge."
    ),
    "auto_marketplace": (
        "You help users with Auto Marketplace: vehicles, CRM, finance, and dealer workflows."
    ),
    "knowledge": "Answer using the shared knowledge graph and cite relevant nodes when possible.",
    "planning": "Break the user's goal into clear, ordered steps before executing.",
}


def render_prompt(
    template_key: str,
    *,
    message: str,
    context: dict[str, Any] | None = None,
    locale: str = "en",
) -> str:
    system = SYSTEM_PROMPTS.get(template_key, SYSTEM_PROMPTS["default"])
    ctx = context or {}
    return (
        f"[system:{locale}] {system}\n"
        f"[context] {ctx}\n"
        f"[user] {message}"
    )


def list_prompts() -> dict[str, str]:
    return dict(SYSTEM_PROMPTS)

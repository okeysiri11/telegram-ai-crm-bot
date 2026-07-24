"""Prompt Gateway — Sprint 24.9."""

from __future__ import annotations

from typing import Any


class PromptGateway:
    def assemble(
        self,
        *,
        template: str,
        system_instructions: str = "",
        brand_dna: dict[str, Any] | None = None,
        enterprise_context: dict[str, Any] | None = None,
        knowledge_graph_refs: list[str] | None = None,
        security_policy: dict[str, Any] | None = None,
        user_prompt: str = "",
    ) -> dict[str, Any]:
        if not template and not user_prompt:
            raise ValueError("template or user_prompt is required")
        policy = dict(security_policy or {"redact_secrets": True, "no_pii_exfil": True})
        return {
            "template": template or "default",
            "system_instructions": system_instructions or None,
            "brand_dna": dict(brand_dna or {}),
            "enterprise_context": dict(enterprise_context or {}),
            "knowledge_graph_refs": list(knowledge_graph_refs or []),
            "security_policy": policy,
            "user_prompt": user_prompt,
            "gateway": True,
            "single_entry_point": True,
        }

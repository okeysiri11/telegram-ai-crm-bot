"""ai_assistant domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class AiAssistantFacade:
    """Scaffold facade for domain `ai_assistant`."""

    domain = "ai_assistant"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}

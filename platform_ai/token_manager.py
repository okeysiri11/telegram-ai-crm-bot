# Token estimation and limits.

from __future__ import annotations


class TokenManager:
    """Estimate token counts (provider-agnostic approximation)."""

    CHARS_PER_TOKEN = 4

    def estimate(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // self.CHARS_PER_TOKEN)

    def estimate_messages(self, messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else str(msg.get("content", ""))
            total += self.estimate(content) + 4
        return total

    def fits_context(self, tokens: int, context_window: int, max_output: int) -> bool:
        return tokens + max_output <= context_window


token_manager = TokenManager()

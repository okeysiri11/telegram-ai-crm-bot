# Platform Memory — token estimation and extractive summarization.

from __future__ import annotations

from platform_memory.models import ConversationTurn


def estimate_tokens(text: str) -> int:
    """Approximate token count (4 chars ≈ 1 token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    if estimate_tokens(text) <= max_tokens:
        return text
    char_limit = max_tokens * 4
    return text[:char_limit].rstrip() + "…"


class MemorySummarizer:
    """Extractive summarizer — pluggable LLM backend can replace later."""

    def summarize_conversation(self, turns: list[ConversationTurn], *, max_tokens: int) -> tuple[str, list[ConversationTurn]]:
        if not turns:
            return "", []

        lines = [f"{t.role}: {t.content}" for t in turns]
        combined = "\n".join(lines)
        if estimate_tokens(combined) <= max_tokens:
            return combined, turns

        head = turns[: max(1, len(turns) // 4)]
        tail = turns[-max(1, len(turns) // 4) :]
        summary_turn = ConversationTurn(
            turn_id="summary",
            session_id=turns[0].session_id,
            role="system",
            content=(
                f"[Summarized {len(turns)} turns — showing first {len(head)} and last {len(tail)}]\n"
                + "\n".join(f"{t.role}: {t.content}" for t in head)
                + "\n...\n"
                + "\n".join(f"{t.role}: {t.content}" for t in tail)
            ),
            user_id=turns[0].user_id,
            agent_id=turns[0].agent_id,
            plugin_id=turns[0].plugin_id,
            metadata={"summarized": True, "original_turn_count": len(turns)},
        )
        condensed = [summary_turn]
        return summary_turn.content, condensed

    def summarize_text(self, text: str, *, max_tokens: int) -> str:
        if estimate_tokens(text) <= max_tokens:
            return text
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
        if not sentences:
            return truncate_to_tokens(text, max_tokens)
        selected: list[str] = []
        used = 0
        for sentence in sentences:
            cost = estimate_tokens(sentence)
            if used + cost > max_tokens:
                break
            selected.append(sentence)
            used += cost
        if not selected:
            return truncate_to_tokens(text, max_tokens)
        return ". ".join(selected) + "."

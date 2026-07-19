# Platform Memory — conversation history repository.

from __future__ import annotations

from platform_memory.exceptions import MemoryValidationError
from platform_memory.models import ConversationRole, ConversationTurn, new_id
from platform_memory.providers.base import ConversationHistoryProvider


class ConversationHistoryRepository:
    """Repository for dialog turns — no direct database access."""

    __slots__ = ("_provider",)

    def __init__(self, provider: ConversationHistoryProvider) -> None:
        self._provider = provider

    async def append_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        plugin_id: str | None = None,
        metadata: dict | None = None,
    ) -> ConversationTurn:
        if not session_id:
            raise MemoryValidationError("session_id is required")
        if not content.strip():
            raise MemoryValidationError("content must not be empty")
        if role not in {r.value for r in ConversationRole}:
            raise MemoryValidationError(f"invalid role: {role}")

        turn = ConversationTurn(
            turn_id=new_id(),
            session_id=session_id,
            role=role,
            content=content,
            user_id=user_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            metadata=dict(metadata or {}),
        )
        return await self._provider.append_turn(turn)

    async def list_history(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        plugin_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationTurn]:
        return await self._provider.list_turns(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            limit=limit,
        )

    async def replace_session_history(self, session_id: str, turns: list[ConversationTurn]) -> None:
        await self._provider.replace_turns(session_id, turns)

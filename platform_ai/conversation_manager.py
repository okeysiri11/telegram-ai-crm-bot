# Conversation history manager.

from __future__ import annotations

from platform_ai.models import AIMessage


class ConversationManager:
    def __init__(self, *, max_messages: int = 100) -> None:
        self._conversations: dict[str, list[AIMessage]] = {}
        self.max_messages = max_messages

    def reset(self) -> None:
        self._conversations.clear()

    def get_or_create(self, conversation_id: str) -> list[AIMessage]:
        return self._conversations.setdefault(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        messages = self.get_or_create(conversation_id)
        messages.append(AIMessage(role=role, content=content))
        if len(messages) > self.max_messages:
            del messages[: len(messages) - self.max_messages]

    def get_messages(self, conversation_id: str) -> list[AIMessage]:
        return list(self._conversations.get(conversation_id, []))

    def clear(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)

    def list_conversations(self) -> list[str]:
        return list(self._conversations.keys())


conversation_manager = ConversationManager()

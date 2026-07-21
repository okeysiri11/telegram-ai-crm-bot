# Conversation management — multi-session, summaries, translation, voice-ready.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.assistant.events import ConversationCreatedEvent
from ecosystem.assistant.models import Conversation, ConversationTurn
from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


TRANSLATIONS = {
    "ru": {"hello": "Здравствуйте", "ready": "Ассистент готов"},
    "en": {"hello": "Hello", "ready": "Assistant ready"},
}


class ConversationService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def create(
        self,
        user_id: str,
        *,
        application_id: str = "",
        organization_id: str = "",
        title: str = "",
        locale: str = "en",
        voice_ready: bool = False,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            application_id=application_id,
            organization_id=organization_id,
            title=title or "New conversation",
            locale=locale,
            voice_ready=voice_ready,
        )
        self._store.conversations.save(conversation.conversation_id, conversation)
        await publish(
            ConversationCreatedEvent(
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                application_id=application_id,
            )
        )
        return conversation

    def get(self, conversation_id: str) -> Conversation:
        conversation = self._store.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation", conversation_id)
        return conversation

    def list_for_user(self, user_id: str) -> list[Conversation]:
        return sorted(
            [c for c in self._store.conversations.list_all() if c.user_id == user_id],
            key=lambda c: c.updated_at,
            reverse=True,
        )

    def append_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        locale: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        conversation = self.get(conversation_id)
        turn = ConversationTurn(
            role=role,
            content=content,
            locale=locale or conversation.locale,
            metadata=metadata or {},
        )
        conversation.turns.append(turn)
        conversation.updated_at = time.time()
        self._store.conversations.save(conversation_id, conversation)
        return conversation

    def summarize(self, conversation_id: str) -> Conversation:
        conversation = self.get(conversation_id)
        if not conversation.turns:
            conversation.summary = ""
        else:
            snippets = [f"{t.role}: {t.content[:80]}" for t in conversation.turns[-6:]]
            conversation.summary = " | ".join(snippets)
        conversation.updated_at = time.time()
        self._store.conversations.save(conversation_id, conversation)
        return conversation

    def restore_context(self, conversation_id: str) -> dict[str, Any]:
        conversation = self.get(conversation_id)
        return {
            "conversation_id": conversation_id,
            "summary": conversation.summary,
            "locale": conversation.locale,
            "application_id": conversation.application_id,
            "turns_count": len(conversation.turns),
            "context_snapshot": dict(conversation.context_snapshot),
            "recent_turns": [t.to_dict() for t in conversation.turns[-5:]],
        }

    def save_context_snapshot(self, conversation_id: str, snapshot: dict[str, Any]) -> Conversation:
        conversation = self.get(conversation_id)
        conversation.context_snapshot.update(snapshot)
        conversation.updated_at = time.time()
        self._store.conversations.save(conversation_id, conversation)
        return conversation

    def translate(self, text: str, *, target_locale: str = "en") -> dict[str, Any]:
        table = TRANSLATIONS.get(target_locale, TRANSLATIONS["en"])
        lowered = text.lower()
        for key, value in table.items():
            if key in lowered:
                return {"original": text, "locale": target_locale, "translated": value, "matched": key}
        return {"original": text, "locale": target_locale, "translated": text, "matched": None}

    def voice_payload(self, conversation_id: str, text: str) -> dict[str, Any]:
        conversation = self.get(conversation_id)
        return {
            "conversation_id": conversation_id,
            "voice_ready": conversation.voice_ready,
            "locale": conversation.locale,
            "text": text,
            "ssml": f"<speak>{text}</speak>",
            "format": "text/ssml",
        }


conversation_service = ConversationService()

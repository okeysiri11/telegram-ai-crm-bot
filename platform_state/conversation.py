"""Unified Conversation Engine — one Conversation entity for all clients (34.2C)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from platform_state.models import EntityMeta, compute_revision, utcnow


@dataclass
class ConversationMessage:
    message_id: str
    role: str  # user | assistant | agent | system
    content: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    source_client: str | None = None
    created_at: str = field(default_factory=lambda: utcnow().isoformat())
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Conversation:
    conversation_id: str
    user_id: str | None = None
    telegram_id: int | None = None
    workspace_id: str | None = None
    participants: list[str] = field(default_factory=list)
    messages: list[ConversationMessage] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    memory_refs: list[str] = field(default_factory=list)
    active_agents: list[str] = field(default_factory=list)
    status: str = "active"  # active | archived | closed
    client_bindings: dict[str, str] = field(default_factory=dict)  # client → external_id
    entity: EntityMeta | None = None

    def __post_init__(self) -> None:
        if self.entity is None:
            self.entity = EntityMeta(
                entity_type="conversation",
                entity_id=self.conversation_id,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "telegram_id": self.telegram_id,
            "workspace_id": self.workspace_id,
            "participants": list(self.participants),
            "messages": [m.to_dict() for m in self.messages],
            "attachments": list(self.attachments),
            "context": dict(self.context),
            "memory_refs": list(self.memory_refs),
            "active_agents": list(self.active_agents),
            "status": self.status,
            "client_bindings": dict(self.client_bindings),
            "entity": self.entity.to_dict() if self.entity else None,
            "message_count": len(self.messages),
        }


class ConversationEngine:
    """
    Canonical conversation store shared by Telegram / Web / Desktop / AI Studio.
    Adapters bind client-specific chat ids via client_bindings.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, Conversation] = {}
        self._by_binding: dict[str, str] = {}  # "telegram:123" → conversation_id

    def _binding_key(self, client: str, external_id: str) -> str:
        return f"{client}:{external_id}"

    def get_or_create(
        self,
        *,
        conversation_id: str | None = None,
        user_id: str | None = None,
        telegram_id: int | None = None,
        workspace_id: str | None = None,
        source_client: str | None = None,
        external_id: str | None = None,
    ) -> Conversation:
        if conversation_id and conversation_id in self._by_id:
            return self._by_id[conversation_id]
        if source_client and external_id:
            key = self._binding_key(source_client, external_id)
            existing = self._by_binding.get(key)
            if existing and existing in self._by_id:
                return self._by_id[existing]
        cid = conversation_id or str(uuid.uuid4())
        conv = Conversation(
            conversation_id=cid,
            user_id=user_id,
            telegram_id=telegram_id,
            workspace_id=workspace_id,
        )
        if source_client and external_id:
            conv.client_bindings[source_client] = external_id
            self._by_binding[self._binding_key(source_client, external_id)] = cid
        self._by_id[cid] = conv
        return conv

    def get(self, conversation_id: str) -> Conversation | None:
        return self._by_id.get(conversation_id)

    def resolve_binding(self, client: str, external_id: str) -> Conversation | None:
        cid = self._by_binding.get(self._binding_key(client, external_id))
        return self._by_id.get(cid) if cid else None

    def append_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        source_client: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        actor_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        conv = self._by_id.get(conversation_id)
        if conv is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            role=role,
            content=content,
            attachments=list(attachments or []),
            source_client=source_client,
            meta=dict(meta or {}),
        )
        conv.messages.append(msg)
        if attachments:
            conv.attachments.extend(attachments)
        if conv.entity:
            conv.entity.bump(updated_by=actor_id, source_client=source_client)
        return msg

    def bind_client(self, conversation_id: str, client: str, external_id: str) -> Conversation:
        conv = self._by_id[conversation_id]
        conv.client_bindings[client] = external_id
        self._by_binding[self._binding_key(client, external_id)] = conversation_id
        if conv.entity:
            conv.entity.bump(source_client=client)
        return conv

    def set_agents(self, conversation_id: str, agents: list[str]) -> Conversation:
        conv = self._by_id[conversation_id]
        conv.active_agents = list(agents)
        if conv.entity:
            conv.entity.bump()
        return conv

    def add_memory_ref(self, conversation_id: str, memory_id: str) -> Conversation:
        conv = self._by_id[conversation_id]
        if memory_id not in conv.memory_refs:
            conv.memory_refs.append(memory_id)
        if conv.entity:
            conv.entity.bump()
        return conv

    def list_for_user(
        self,
        *,
        user_id: str | None = None,
        telegram_id: int | None = None,
        limit: int = 50,
    ) -> list[Conversation]:
        out: list[Conversation] = []
        for conv in self._by_id.values():
            if user_id and conv.user_id == user_id:
                out.append(conv)
            elif telegram_id is not None and conv.telegram_id == telegram_id:
                out.append(conv)
        return out[:limit]

    def revision_token(self) -> str:
        parts = [
            (c.conversation_id, c.entity.version if c.entity else 0, len(c.messages))
            for c in self._by_id.values()
        ]
        return compute_revision(parts)

    def snapshot(self, *, user_id: str | None = None, telegram_id: int | None = None) -> dict[str, Any]:
        items = self.list_for_user(user_id=user_id, telegram_id=telegram_id, limit=100)
        if user_id is None and telegram_id is None:
            items = list(self._by_id.values())[:100]
        return {
            "count": len(items),
            "revision": self.revision_token(),
            "conversations": [c.to_dict() for c in items],
        }

    def reset(self) -> None:
        self._by_id.clear()
        self._by_binding.clear()


conversation_engine = ConversationEngine()

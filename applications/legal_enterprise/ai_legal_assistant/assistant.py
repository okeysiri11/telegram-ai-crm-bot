"""AI Legal Assistant — chat, Q&A, multi-turn dialogue, workspace."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegalAssistant:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def create_workspace(self, *, name: str, owner: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("workspace name required")
        wid = _id("aa_ws")
        return self.store.aa_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "name": name,
                "owner": owner or "counsel",
                "created_at": _now(),
            },
        )

    def start_conversation(
        self, *, workspace_id: str = "", title: str = "Legal consultation"
    ) -> dict[str, Any]:
        if workspace_id and self.store.aa_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        cid = _id("aa_conv")
        return self.store.aa_conversations.save(
            cid,
            {
                "conversation_id": cid,
                "workspace_id": workspace_id,
                "title": title,
                "turns": 0,
                "created_at": _now(),
            },
        )

    def ask(
        self,
        *,
        question: str,
        conversation_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not question:
            raise ValidationError("question required")
        if conversation_id and self.store.aa_conversations.get(conversation_id) is None:
            raise NotFoundError("conversation", conversation_id)
        answer = (
            f"Based on applicable authorities, the legal position regarding "
            f"'{question[:120]}' requires analysis of statutes, case law, and contractual context."
        )
        mid = _id("aa_msg")
        row = self.store.aa_messages.save(
            mid,
            {
                "message_id": mid,
                "conversation_id": conversation_id,
                "role": "assistant",
                "question": question,
                "answer": answer,
                "context": context or {},
                "at": _now(),
            },
        )
        if conversation_id:
            conv = self.store.aa_conversations.get(conversation_id)
            if conv:
                conv["turns"] = int(conv.get("turns", 0)) + 1
                self.store.aa_conversations.save(conversation_id, conv)
            self.remember(conversation_id=conversation_id, key="last_question", value=question)
        return row

    def chat(
        self, *, conversation_id: str, message: str, role: str = "user"
    ) -> dict[str, Any]:
        if self.store.aa_conversations.get(conversation_id) is None:
            raise NotFoundError("conversation", conversation_id)
        if not message:
            raise ValidationError("message required")
        uid = _id("aa_chat")
        user_msg = self.store.aa_messages.save(
            uid,
            {
                "message_id": uid,
                "conversation_id": conversation_id,
                "role": role,
                "content": message,
                "at": _now(),
            },
        )
        if role == "user":
            reply = self.ask(question=message, conversation_id=conversation_id)
            return {"user": user_msg, "assistant": reply}
        return user_msg

    def remember(self, *, conversation_id: str, key: str, value: Any) -> dict[str, Any]:
        if self.store.aa_conversations.get(conversation_id) is None:
            raise NotFoundError("conversation", conversation_id)
        if not key:
            raise ValidationError("key required")
        mid = _id("aa_mem")
        return self.store.aa_memory.save(
            mid,
            {
                "memory_id": mid,
                "conversation_id": conversation_id,
                "key": key,
                "value": value,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "workspaces": self.store.aa_workspaces.count(),
            "conversations": self.store.aa_conversations.count(),
            "messages": self.store.aa_messages.count(),
            "memory": self.store.aa_memory.count(),
        }

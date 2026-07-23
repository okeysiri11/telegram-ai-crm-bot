"""AI CFO workspace — chat, Q&A, context analysis, conversation history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AICFOWorkspace:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.roles = list(DEFAULT_CONFIG.cfo_assistant_roles)

    def open_workspace(self, *, label: str, owner: str = "cfo") -> dict[str, Any]:
        if not label:
            raise ValidationError("label required")
        wid = _id("cfo_ws")
        return self.store.cfo_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "label": label,
                "owner": owner,
                "status": "active",
                "at": _now(),
            },
        )

    def chat(
        self,
        *,
        workspace_id: str,
        message: str,
        role: str = "executive_assistant",
        context: str = "",
    ) -> dict[str, Any]:
        if self.store.cfo_workspaces.get(workspace_id) is None:
            raise NotFoundError(f"workspace not found: {workspace_id}")
        r = role.lower().strip()
        if r not in self.roles:
            raise ValidationError(f"role must be one of {self.roles}")
        if not message:
            raise ValidationError("message required")
        cid = _id("cfo_chat")
        reply = f"AI CFO ({r}): analyzed '{message[:80]}'" + (f" with context {context}" if context else "")
        return self.store.cfo_conversations.save(
            cid,
            {
                "conversation_id": cid,
                "workspace_id": workspace_id,
                "role": r,
                "message": message,
                "reply": reply,
                "context": context,
                "at": _now(),
            },
        )

    def ask(self, *, workspace_id: str, question: str) -> dict[str, Any]:
        if not question:
            raise ValidationError("question required")
        return self.chat(
            workspace_id=workspace_id,
            message=question,
            role="qa",
            context="financial_qa",
        )

    def status(self) -> dict[str, Any]:
        return {
            "workspaces": self.store.cfo_workspaces.count(),
            "conversations": self.store.cfo_conversations.count(),
            "roles": self.roles,
        }

"""Enterprise AI Concierge wizard — Sprint 28.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.concierge.catalogs import (
    COMMUNICATION_STYLES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.concierge.registry import ConciergeRegistry
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ConciergeWizard:
    """Visual wizard for creating the organization's single AI Concierge."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.registry = ConciergeRegistry(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "builder_id": "concierge",
            "version": "1.2.0",
            "sprint": "28.3",
            "operational": True,
            "not_an_ai_agent": True,
            **full_catalog(),
        }

    def start_session(self, *, organization_id: str = "org_demo") -> dict[str, Any]:
        org = (organization_id or "").strip() or "org_demo"
        existing = self.registry.get_for_organization(org)
        sid = _id("cwiz")
        record = {
            "session_id": sid,
            "organization_id": org,
            "status": "in_progress",
            "step": 1,
            "existing_concierge_id": existing["concierge_id"] if existing else None,
            "draft": {
                "name": "",
                "avatar": "avatar_exec",
                "gender": "neutral",
                "voice_profile": "clear",
                "communication_style": "professional",
                "role": None,
                "role_custom": "",
                "organization_access": [],
                "orchestration": [],
                "proactive": [],
                "owner_relationship": "balanced",
                "recommendations": [],
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.concierge_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.concierge_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Concierge session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 9:
                raise ValidationError("step must be between 1 and 9")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        if "organization_id" in patch and patch["organization_id"]:
            session["organization_id"] = str(patch["organization_id"]).strip()
        session["updated_at"] = _now()
        self.store.concierge_sessions.save(session_id, session)
        return session

    def conversation_preview(self, draft: dict[str, Any] | None = None) -> dict[str, Any]:
        data = draft or {}
        name = (data.get("name") or "Concierge").strip() or "Concierge"
        style = data.get("communication_style") or "professional"
        sample = next(
            (s["sample"] for s in COMMUNICATION_STYLES if s["id"] == style),
            COMMUNICATION_STYLES[1]["sample"],
        )
        return {
            "name": name,
            "style": style,
            "preview": [
                {"role": "owner", "text": "What should I focus on today?"},
                {"role": "concierge", "text": f"{name}: {sample}"},
            ],
            "note": "AI Concierge is the central intelligence of the organization — not an AI Agent.",
        }

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        return {
            "session_id": session_id,
            "organization_id": session["organization_id"],
            "title": "Concierge Card",
            "card": {
                "identity": {
                    "name": draft.get("name"),
                    "avatar": draft.get("avatar"),
                    "gender": draft.get("gender"),
                    "voice_profile": draft.get("voice_profile"),
                    "communication_style": draft.get("communication_style"),
                },
                "role": draft.get("role_custom") if draft.get("role") == "custom" else draft.get("role"),
                "permissions": draft.get("organization_access") or [],
                "organization_access": draft.get("organization_access") or [],
                "proactive_functions": draft.get("proactive") or [],
                "orchestration": draft.get("orchestration") or [],
                "owner_relationship": draft.get("owner_relationship"),
                "recommendations": draft.get("recommendations") or [],
                "communication_style": draft.get("communication_style"),
            },
            "rules": {
                "one_per_organization": True,
                "not_an_ai_agent": True,
            },
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        name = (draft.get("name") or "").strip()
        if not name:
            raise ValidationError("Concierge name is required")
        role = draft.get("role") or draft.get("role_custom")
        if not role:
            raise ValidationError("Concierge role is required")
        if session.get("existing_concierge_id"):
            raise ValidationError(
                "This organization already has a Concierge. Only one Concierge is allowed."
            )
        record = self.registry.register(
            {
                "name": name,
                "avatar": draft.get("avatar"),
                "gender": draft.get("gender"),
                "voice_profile": draft.get("voice_profile"),
                "communication_style": draft.get("communication_style"),
                "role": role if role != "custom" else (draft.get("role_custom") or "custom"),
                "organization_id": session["organization_id"],
                "organization_access": draft.get("organization_access") or [],
                "orchestration": draft.get("orchestration") or [],
                "proactive": draft.get("proactive") or [],
                "owner_relationship": draft.get("owner_relationship") or "balanced",
                "recommendations": draft.get("recommendations") or [],
                "recommendations_architecture_only": True,
                "configuration_saved": True,
                "session_id": session_id,
            }
        )
        session["status"] = "created"
        session["created_concierge_id"] = record["concierge_id"]
        session["updated_at"] = _now()
        self.store.concierge_sessions.save(session_id, session)
        return {
            "ok": True,
            "session_id": session_id,
            "concierge": record,
            "registry": self.registry.list_all(),
            "organization_link": self.store.organization_links.get(session["organization_id"]),
            "message": "Concierge created, linked to the organization, and registered in the Concierge Registry.",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "wizard_steps": len(WIZARD_STEPS),
            "sessions": len(self.store.concierge_sessions.list_all()),
            "registered": len(self.store.concierge_registry.list_all()),
            "one_per_organization": True,
            "not_an_ai_agent": True,
        }

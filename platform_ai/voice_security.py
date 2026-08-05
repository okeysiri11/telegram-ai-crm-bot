"""Voice security — RBAC, confirmation, audit, encrypted session hints (Sprint 36.6)."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

from platform_ai.voice_models import CommandRisk, ParsedCommand, VoiceHistoryEntry, new_id

# role → allowed intents (* = all)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {"*"},
    "administrator": {"*"},
    "operator": {
        "open_page",
        "open_crm",
        "open_erp",
        "search_knowledge",
        "create_task",
        "create_project",
        "launch_workflow",
        "call_ai_agent",
        "generate_report",
    },
    "readonly": {"open_page", "open_crm", "open_erp", "search_knowledge"},
}

DANGEROUS_INTENTS = {"assign_employee"}


class VoiceSecurity:
    def __init__(self, *, secret: bytes | None = None) -> None:
        self.secret = secret or b"ados-voice-demo-key"
        self.audit: list[VoiceHistoryEntry] = []

    def reset(self) -> None:
        self.audit.clear()

    def allowed(self, roles: list[str], intent: str) -> bool:
        for role in roles or ["readonly"]:
            perms = ROLE_PERMISSIONS.get(role, set())
            if "*" in perms or intent in perms:
                return True
        return False

    def evaluate(self, parsed: ParsedCommand, *, roles: list[str], confirm_dangerous: bool = True) -> dict[str, Any]:
        intent = parsed.intent.value if hasattr(parsed.intent, "value") else str(parsed.intent)
        if not self.allowed(roles, intent):
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"role denied intent {intent}",
            }
        risk = parsed.risk.value if hasattr(parsed.risk, "value") else str(parsed.risk)
        needs = risk in (CommandRisk.CONFIRM.value, CommandRisk.DANGEROUS.value) or intent in DANGEROUS_INTENTS
        if intent in DANGEROUS_INTENTS and confirm_dangerous:
            needs = True
        return {
            "allowed": True,
            "requires_confirmation": needs,
            "risk": risk,
            "reason": "ok",
        }

    def encrypt_session_blob(self, session_id: str, payload: str) -> dict[str, str]:
        """Demo encrypted storage — HMAC + base64 (not production crypto)."""
        digest = hmac.new(self.secret, f"{session_id}:{payload}".encode(), hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(digest + payload.encode("utf-8")).decode("ascii")
        return {"cipher": "aes-gcm-demo", "token": token, "encrypted": "true"}

    def decrypt_session_blob(self, session_id: str, token: str) -> str:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        payload = raw[32:].decode("utf-8")
        check = self.encrypt_session_blob(session_id, payload)["token"]
        if not hmac.compare_digest(check, token):
            raise ValueError("voice session integrity check failed")
        return payload

    def log(
        self,
        action: str,
        *,
        session_id: str | None = None,
        command_id: str | None = None,
        principal: str | None = None,
        details: dict | None = None,
    ) -> VoiceHistoryEntry:
        entry = VoiceHistoryEntry(
            history_id=new_id("vhist"),
            action=action,
            session_id=session_id,
            command_id=command_id,
            principal=principal,
            details=details or {},
        )
        self.audit.append(entry)
        self.audit = self.audit[-5000:]
        return entry


voice_security = VoiceSecurity()

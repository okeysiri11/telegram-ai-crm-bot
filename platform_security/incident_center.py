# Incident Center — Sprint 32.4. Extends IncidentResponse with emergency controls.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from platform_security.incident_response import IncidentResponse


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentCenter:
    def __init__(self, base: IncidentResponse | None = None) -> None:
        self._base = base or IncidentResponse()
        self.emergency_mode = False
        self._actions: list[dict[str, Any]] = []
        self._disabled_api_keys: set[str] = set()
        self._disabled_providers: set[str] = set()
        self._killed_sessions: set[str] = set()
        self._revoked_tokens: set[str] = set()

    def reset(self) -> None:
        self._base = IncidentResponse()
        self.emergency_mode = False
        self._actions.clear()
        self._disabled_api_keys.clear()
        self._disabled_providers.clear()
        self._killed_sessions.clear()
        self._revoked_tokens.clear()

    def open(self, *, title: str, severity: str = "high", source: str = "monitoring") -> dict[str, Any]:
        return self._base.open(title=title, severity=severity, source=source)

    def list_open(self) -> list[dict[str, Any]]:
        return self._base.list_open()

    def _log(self, action: str, **meta: Any) -> dict[str, Any]:
        row = {"action": action, "at": _now(), **meta, "id": f"act_{uuid.uuid4().hex[:10]}"}
        self._actions.append(row)
        return row

    def auto_lock(self, *, reason: str) -> dict[str, Any]:
        self.emergency_mode = True
        return self._log("auto_lock", reason=reason)

    def enable_emergency_mode(self, *, reason: str) -> dict[str, Any]:
        self.emergency_mode = True
        return self._log("emergency_mode", reason=reason)

    def kill_session(self, session_id: str) -> dict[str, Any]:
        self._killed_sessions.add(session_id)
        return self._log("kill_session", session_id=session_id)

    def revoke_token(self, token_id: str) -> dict[str, Any]:
        self._revoked_tokens.add(token_id)
        return self._log("revoke_token", token_id=token_id)

    def disable_api_key(self, key_id: str) -> dict[str, Any]:
        self._disabled_api_keys.add(key_id)
        return self._log("disable_api_key", key_id=key_id)

    def disable_ai_provider(self, provider: str) -> dict[str, Any]:
        self._disabled_providers.add(provider)
        return self._log("disable_ai_provider", provider=provider)

    def escalate(self, incident_id: str, *, to: str = "security_oncall") -> dict[str, Any]:
        return self._log("threat_escalation", incident_id=incident_id, to=to)

    def is_api_key_disabled(self, key_id: str) -> bool:
        return key_id in self._disabled_api_keys or self.emergency_mode

    def is_provider_disabled(self, provider: str) -> bool:
        return provider in self._disabled_providers or self.emergency_mode

    def action_log(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self._actions[-limit:]

    def capabilities(self) -> dict[str, Any]:
        return {
            "auto_lock": True,
            "emergency_mode": True,
            "kill_sessions": True,
            "revoke_tokens": True,
            "disable_api_keys": True,
            "disable_ai_providers": True,
            "threat_escalation": True,
        }

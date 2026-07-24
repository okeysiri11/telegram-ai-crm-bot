from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.command_center.action_center import ActionCenter


class CommandDispatcher:
    """Routes executive NL / structured commands into Action Center."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.actions = ActionCenter(self.store)

    def dispatch_command(self, *, command: str, actor: str = "executive") -> dict[str, Any]:
        if not command or not str(command).strip():
            raise ValidationError("command is required")
        text = str(command).strip().lower()
        if "workflow" in text or "запуск" in text:
            kind = "start_workflow"
        elif "approv" in text or "соглас" in text:
            kind = "approve"
        elif "simulat" in text or "модел" in text:
            kind = "run_simulation"
        elif "agent" in text:
            kind = "manage_ai_agent"
        elif "incident" in text:
            kind = "manage_incident"
        elif "replay" in text or "сценар" in text:
            kind = "replay_scenario"
        else:
            kind = "assign_task"
        action = self.actions.dispatch(kind=kind, payload={"command": command}, actor=actor)
        cid = _id("ecc_cmd")
        record = {
            "command_id": cid,
            "command": command,
            "action_id": action["action_id"],
            "resolved_kind": kind,
            "actor": actor,
            "dispatched_at": _now(),
        }
        self.store.ecc_commands.save(cid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"commands": len(self.store.ecc_commands.list_all())}

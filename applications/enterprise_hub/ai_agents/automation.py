"""Autonomous automation — scheduled, event-driven, rule-based, approval, HITL, emergency stop."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AutonomousAutomation:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.kinds = list(DEFAULT_CONFIG.aa_automation_kinds)

    def create(
        self,
        *,
        name: str,
        kind: str,
        agent_id: str = "",
        rule: str = "",
        schedule: str = "",
        event: str = "",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        if not name:
            raise ValidationError("name required")
        if agent_id and self.store.aa_agents.get(agent_id) is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        aid = _id("aa_auto")
        return self.store.aa_automations.save(
            aid,
            {
                "automation_id": aid,
                "name": name,
                "kind": k,
                "agent_id": agent_id,
                "rule": rule,
                "schedule": schedule,
                "event": event,
                "status": "active",
                "emergency_stopped": False,
                "at": _now(),
            },
        )

    def request_approval(self, *, automation_id: str, requester: str = "system") -> dict[str, Any]:
        auto = self.store.aa_automations.get(automation_id)
        if auto is None:
            raise NotFoundError(f"automation not found: {automation_id}")
        pid = _id("aa_appr")
        return self.store.aa_approvals.save(
            pid,
            {
                "approval_id": pid,
                "automation_id": automation_id,
                "requester": requester,
                "status": "pending",
                "at": _now(),
            },
        )

    def human_in_loop(
        self, *, automation_id: str, operator: str, decision: str = "continue"
    ) -> dict[str, Any]:
        if self.store.aa_automations.get(automation_id) is None:
            raise NotFoundError(f"automation not found: {automation_id}")
        hid = _id("aa_hitl")
        return self.store.aa_hitl.save(
            hid,
            {
                "hitl_id": hid,
                "automation_id": automation_id,
                "operator": operator or "operator",
                "decision": decision,
                "at": _now(),
            },
        )

    def emergency_stop(self, *, automation_id: str, reason: str = "") -> dict[str, Any]:
        auto = self.store.aa_automations.get(automation_id)
        if auto is None:
            raise NotFoundError(f"automation not found: {automation_id}")
        auto["status"] = "stopped"
        auto["emergency_stopped"] = True
        auto["at"] = _now()
        self.store.aa_automations.save(automation_id, auto)
        eid = _id("aa_estop")
        return self.store.aa_emergency_stops.save(
            eid,
            {
                "stop_id": eid,
                "automation_id": automation_id,
                "reason": reason,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "automations": self.store.aa_automations.count(),
            "approvals": self.store.aa_approvals.count(),
            "hitl": self.store.aa_hitl.count(),
            "emergency_stops": self.store.aa_emergency_stops.count(),
            "kinds": self.kinds,
        }

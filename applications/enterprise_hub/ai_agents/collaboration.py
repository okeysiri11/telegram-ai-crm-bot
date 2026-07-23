"""Multi-agent collaboration — A2A, shared context, delegation, consensus, conflict, planning."""

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


class MultiAgentCollaboration:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def communicate(
        self, *, from_agent_id: str, to_agent_id: str, message: str
    ) -> dict[str, Any]:
        if self.store.aa_agents.get(from_agent_id) is None:
            raise NotFoundError(f"agent not found: {from_agent_id}")
        if self.store.aa_agents.get(to_agent_id) is None:
            raise NotFoundError(f"agent not found: {to_agent_id}")
        if not message:
            raise ValidationError("message required")
        mid = _id("aa_msg")
        return self.store.aa_messages.save(
            mid,
            {
                "message_id": mid,
                "from_agent_id": from_agent_id,
                "to_agent_id": to_agent_id,
                "message": message,
                "at": _now(),
            },
        )

    def share_context(
        self, *, agent_ids: list[str], label: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not agent_ids:
            raise ValidationError("agent_ids required")
        for aid in agent_ids:
            if self.store.aa_agents.get(aid) is None:
                raise NotFoundError(f"agent not found: {aid}")
        cid = _id("aa_ctx")
        return self.store.aa_shared_contexts.save(
            cid,
            {
                "context_id": cid,
                "agent_ids": list(agent_ids),
                "label": label or "shared",
                "payload": payload or {},
                "at": _now(),
            },
        )

    def delegate(
        self, *, from_agent_id: str, to_agent_id: str, task_ref: str
    ) -> dict[str, Any]:
        if self.store.aa_agents.get(from_agent_id) is None:
            raise NotFoundError(f"agent not found: {from_agent_id}")
        if self.store.aa_agents.get(to_agent_id) is None:
            raise NotFoundError(f"agent not found: {to_agent_id}")
        if not task_ref:
            raise ValidationError("task_ref required")
        did = _id("aa_del")
        return self.store.aa_delegations.save(
            did,
            {
                "delegation_id": did,
                "from_agent_id": from_agent_id,
                "to_agent_id": to_agent_id,
                "task_ref": task_ref,
                "at": _now(),
            },
        )

    def consensus(
        self, *, agent_ids: list[str], topic: str, outcome: str = "approved"
    ) -> dict[str, Any]:
        if not agent_ids or not topic:
            raise ValidationError("agent_ids and topic required")
        cid = _id("aa_cons")
        return self.store.aa_consensus.save(
            cid,
            {
                "consensus_id": cid,
                "agent_ids": list(agent_ids),
                "topic": topic,
                "outcome": outcome,
                "at": _now(),
            },
        )

    def resolve_conflict(
        self, *, detail: str, resolution: str = "escalate"
    ) -> dict[str, Any]:
        if not detail:
            raise ValidationError("detail required")
        cid = _id("aa_conf")
        return self.store.aa_collab_conflicts.save(
            cid,
            {
                "conflict_id": cid,
                "detail": detail,
                "resolution": resolution,
                "at": _now(),
            },
        )

    def plan(
        self, *, agent_ids: list[str], objective: str, steps: list[str] | None = None
    ) -> dict[str, Any]:
        if not agent_ids or not objective:
            raise ValidationError("agent_ids and objective required")
        pid = _id("aa_plan")
        return self.store.aa_plans.save(
            pid,
            {
                "plan_id": pid,
                "agent_ids": list(agent_ids),
                "objective": objective,
                "steps": steps or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "messages": self.store.aa_messages.count(),
            "shared_contexts": self.store.aa_shared_contexts.count(),
            "delegations": self.store.aa_delegations.count(),
            "consensus": self.store.aa_consensus.count(),
            "conflicts": self.store.aa_collab_conflicts.count(),
            "plans": self.store.aa_plans.count(),
        }

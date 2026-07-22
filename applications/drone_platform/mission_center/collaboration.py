"""Multi-operator collaboration (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


OPERATOR_ROLES = (
    "supervisor",
    "mission_commander",
    "payload_operator",
    "observer",
    "maintenance_engineer",
    "operator",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CollaborationService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register_operator(self, *, name: str, role: str) -> dict[str, Any]:
        role = role.lower().strip()
        if role not in OPERATOR_ROLES:
            raise ValidationError(f"Unsupported role: {role}")
        oid = f"opr_{uuid.uuid4().hex[:12]}"
        op = {"operator_id": oid, "name": name, "role": role, "created_at": _now()}
        self.store.operators.save(oid, op)
        return op

    def list_operators(self) -> list[dict[str, Any]]:
        return self.store.operators.list_all()

    def add_comment(self, *, ops_mission_id: str, operator_id: str, text: str) -> dict[str, Any]:
        cid = f"cmt_{uuid.uuid4().hex[:12]}"
        comment = {
            "comment_id": cid,
            "ops_mission_id": ops_mission_id,
            "operator_id": operator_id,
            "text": text,
            "created_at": _now(),
        }
        self.store.mission_comments.save(cid, comment)
        return comment

    def list_comments(self, ops_mission_id: str) -> list[dict[str, Any]]:
        return [c for c in self.store.mission_comments.list_all() if c.get("ops_mission_id") == ops_mission_id]

    def shared_edit(self, ops_mission: dict[str, Any], *, operator_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        for key in ("name", "waypoints", "priority", "metadata"):
            if key in patch:
                ops_mission[key] = patch[key]
        ops_mission.setdefault("timeline", []).append({"event": "shared_edit", "operator_id": operator_id, "at": _now()})
        return ops_mission

    def request_approval(self, *, ops_mission_id: str, requester_id: str) -> dict[str, Any]:
        aid = f"apr_{uuid.uuid4().hex[:12]}"
        item = {
            "approval_id": aid,
            "ops_mission_id": ops_mission_id,
            "requester_id": requester_id,
            "status": "pending",
            "created_at": _now(),
        }
        self.store.mission_approvals.save(aid, item)
        return item

    def decide_approval(self, approval_id: str, *, approver_id: str, approved: bool, notes: str = "") -> dict[str, Any]:
        item = self.store.mission_approvals.get(approval_id)
        if item is None:
            raise NotFoundError("mission_approval", approval_id)
        item["status"] = "approved" if approved else "rejected"
        item["approver_id"] = approver_id
        item["notes"] = notes
        item["decided_at"] = _now()
        self.store.mission_approvals.save(approval_id, item)
        return item

    def status(self) -> dict[str, Any]:
        return {
            "collaboration": "1.0",
            "roles": list(OPERATOR_ROLES),
            "operators": self.store.operators.count(),
            "comments": self.store.mission_comments.count(),
            "approvals": self.store.mission_approvals.count(),
            "capabilities": [
                "operator_roles",
                "shared_mission_editing",
                "mission_comments",
                "mission_approval_workflow",
            ],
        }


collaboration_service = CollaborationService()

"""Membership Center portal view — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class MembershipCenter:
    def view(self, memberships: list[dict[str, Any]]) -> dict[str, Any]:
        active = [m for m in memberships if m.get("status") == "active"]
        renewals = [
            {
                "membership_id": m.get("membership_id"),
                "recommend_renew": int(m.get("visits_remaining", 0)) <= 2,
            }
            for m in memberships
        ]
        return {
            "active": active,
            "remaining_visits": [m.get("visits_remaining") for m in active],
            "renewal_recommendations": renewals,
            "commerce_ref": "commerce_core",
        }

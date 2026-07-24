"""Membership Engine — Sprint 22.7."""

from __future__ import annotations

from typing import Any


class MembershipEngine:
    def create(
        self,
        *,
        customer_id: str,
        visits_limit: int = 10,
        name: str = "standard",
    ) -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        if visits_limit <= 0:
            raise ValueError("visits_limit must be positive")
        return {
            "customer_id": customer_id,
            "name": name,
            "visits_limit": visits_limit,
            "visits_remaining": visits_limit,
            "restrictions": [],
            "status": "active",
            "auto_debit": True,
            "renewable": True,
            "notify_on_low": True,
        }

    def debit(self, membership: dict[str, Any], *, visits: int = 1) -> dict[str, Any]:
        remaining = int(membership.get("visits_remaining", 0)) - int(visits)
        if remaining < 0:
            raise ValueError("membership visit limit exceeded")
        updated = dict(membership)
        updated["visits_remaining"] = remaining
        if remaining == 0:
            updated["status"] = "exhausted"
            updated["notification"] = "membership_ending"
        return updated

    def renew(self, membership: dict[str, Any], *, visits_limit: int | None = None) -> dict[str, Any]:
        limit = int(visits_limit or membership.get("visits_limit", 10))
        updated = dict(membership)
        updated["visits_limit"] = limit
        updated["visits_remaining"] = limit
        updated["status"] = "active"
        updated["notification"] = "membership_renewed"
        return updated

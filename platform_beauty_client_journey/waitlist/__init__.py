"""Waitlist Manager — Sprint 22.4."""

from __future__ import annotations

from typing import Any


class WaitlistManager:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def join(
        self,
        *,
        customer_id: str,
        service_ids: list[str],
        preferred_windows: list[str] | None = None,
    ) -> dict[str, Any]:
        if not customer_id or not service_ids:
            raise ValueError("customer_id and service_ids required")
        entry = {
            "customer_id": customer_id,
            "service_ids": list(service_ids),
            "preferred_windows": list(preferred_windows or []),
            "status": "waiting",
            "notified_client": False,
            "notified_admin": False,
        }
        self._entries.append(entry)
        return entry

    def offer_slot(self, *, customer_id: str, slot: dict[str, Any]) -> dict[str, Any]:
        for entry in self._entries:
            if entry["customer_id"] == customer_id and entry["status"] == "waiting":
                entry["status"] = "offered"
                entry["offered_slot"] = slot
                entry["notified_client"] = True
                entry["notified_admin"] = True
                return {
                    "offered": True,
                    "entry": entry,
                    "notify_client": True,
                    "notify_admin": True,
                    "auto_booked": False,
                }
        raise ValueError(f"no waitlist entry for customer: {customer_id}")

    def list_waiting(self) -> list[dict[str, Any]]:
        return [e for e in self._entries if e["status"] == "waiting"]

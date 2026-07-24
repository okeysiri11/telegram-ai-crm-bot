"""Reminder Center — Sprint 22.4."""

from __future__ import annotations

from typing import Any

from platform_beauty_client_journey.models import REMINDER_CHANNELS, REMINDER_KINDS


class ReminderCenter:
    def schedule(
        self,
        *,
        kind: str,
        channel: str,
        customer_id: str,
        appointment_id: str = "",
    ) -> dict[str, Any]:
        if kind not in REMINDER_KINDS:
            raise ValueError(f"unknown reminder kind: {kind}")
        if channel not in REMINDER_CHANNELS:
            raise ValueError(f"unknown reminder channel: {channel}")
        if not customer_id:
            raise ValueError("customer_id required")
        return {
            "kind": kind,
            "channel": channel,
            "customer_id": customer_id,
            "appointment_id": appointment_id,
            "status": "scheduled",
            "comms_ref": "enterprise_communications",
            "whatsapp_connector": "future" if channel == "whatsapp" else None,
        }

    def seed_for_booking(self, *, customer_id: str, appointment_id: str) -> list[dict[str, Any]]:
        plan = [
            ("day_before", "sms"),
            ("hours_before", "telegram"),
            ("after_visit", "push"),
            ("rebook_invite", "email"),
        ]
        return [
            self.schedule(kind=k, channel=c, customer_id=customer_id, appointment_id=appointment_id)
            for k, c in plan
        ]

"""Court calendar — hearings, courtrooms, reminders, recurring events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CourtCalendar:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register_courtroom(
        self, *, name: str, building: str = "", capacity: int = 0
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("courtroom name required")
        rid = _id("cm_room")
        return self.store.cm_courtrooms.save(
            rid,
            {
                "courtroom_id": rid,
                "name": name,
                "building": building,
                "capacity": int(capacity or 0),
                "created_at": _now(),
            },
        )

    def schedule_hearing(
        self,
        *,
        case_id: str,
        title: str,
        scheduled_at: str,
        judge_name: str = "",
        courtroom_id: str = "",
        hearing_type: str = "hearing",
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title or not scheduled_at:
            raise ValidationError("title and scheduled_at required")
        if courtroom_id and self.store.cm_courtrooms.get(courtroom_id) is None:
            raise NotFoundError("courtroom", courtroom_id)
        hid = _id("cm_hear")
        return self.store.cm_hearings.save(
            hid,
            {
                "hearing_id": hid,
                "case_id": case_id,
                "title": title,
                "scheduled_at": scheduled_at,
                "judge_name": judge_name,
                "courtroom_id": courtroom_id,
                "hearing_type": hearing_type,
                "status": "scheduled",
                "created_at": _now(),
            },
        )

    def assign_judge(self, *, hearing_id: str, judge_name: str) -> dict[str, Any]:
        hearing = self.store.cm_hearings.get(hearing_id)
        if hearing is None:
            raise NotFoundError("hearing", hearing_id)
        if not judge_name:
            raise ValidationError("judge_name required")
        hearing["judge_name"] = judge_name
        self.store.cm_hearings.save(hearing_id, hearing)
        return hearing

    def sync_calendar(self, *, source: str = "court_system", events: int = 0) -> dict[str, Any]:
        sid = _id("cm_sync")
        return self.store.cm_calendar_syncs.save(
            sid,
            {
                "sync_id": sid,
                "source": source,
                "events_synced": int(events or self.store.cm_hearings.count()),
                "at": _now(),
            },
        )

    def create_reminder(
        self, *, hearing_id: str, remind_at: str, channel: str = "email"
    ) -> dict[str, Any]:
        if self.store.cm_hearings.get(hearing_id) is None:
            raise NotFoundError("hearing", hearing_id)
        if not remind_at:
            raise ValidationError("remind_at required")
        rid = _id("cm_rem")
        return self.store.cm_reminders.save(
            rid,
            {
                "reminder_id": rid,
                "hearing_id": hearing_id,
                "remind_at": remind_at,
                "channel": channel,
                "status": "pending",
                "at": _now(),
            },
        )

    def recurring_event(
        self,
        *,
        case_id: str,
        title: str,
        cadence: str = "weekly",
        next_at: str = "",
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title:
            raise ValidationError("title required")
        rid = _id("cm_rec")
        return self.store.cm_recurring.save(
            rid,
            {
                "recurring_id": rid,
                "case_id": case_id,
                "title": title,
                "cadence": cadence,
                "next_at": next_at,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "courtrooms": self.store.cm_courtrooms.count(),
            "hearings": self.store.cm_hearings.count(),
            "syncs": self.store.cm_calendar_syncs.count(),
            "reminders": self.store.cm_reminders.count(),
            "recurring": self.store.cm_recurring.count(),
        }

"""Beauty Client Journey Suite facade — Sprint 22.4 / v6.5.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_beauty_client_journey.facade import BeautyClientJourneyLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BeautyClientJourneySuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = BeautyClientJourneyLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = BeautyClientJourneyLibrary()
        if not self.store.bos_customers.list_all():
            try:
                from applications.enterprise_hub import enterprise_hub

                enterprise_hub.beauty_os.bootstrap()
            except Exception:
                pass
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("bcj_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.bcj_bootstraps.save(bid, record)
        jid = _id("bcj_jrn")
        self.store.bcj_journeys.save(jid, {"journey_id": jid, **full["journey"], "created_at": _now()})
        bk = _id("bcj_bk")
        self.store.bcj_bookings.save(bk, {"booking_id": bk, **full["booking"], "created_at": _now()})
        aid = _id("bcj_av")
        self.store.bcj_availability.save(aid, {"availability_id": aid, **full["availability"], "created_at": _now()})
        asid = _id("bcj_ai")
        self.store.bcj_assistant.save(asid, {"assistant_id": asid, **full["assistant"], "created_at": _now()})
        for rem in full["reminders"]:
            rid = _id("bcj_rem")
            self.store.bcj_reminders.save(rid, {"reminder_id": rid, **rem, "created_at": _now()})
        wid = _id("bcj_wl")
        self.store.bcj_waitlist.save(wid, {"waitlist_id": wid, **full["waitlist"], "created_at": _now()})
        lid = _id("bcj_loy")
        self.store.bcj_loyalty.save(lid, {"loyalty_id": lid, **full["loyalty"], "created_at": _now()})
        record["journey_id"] = jid
        record["booking_id"] = bk
        record["assistant_id"] = asid
        self.store.bcj_bootstraps.save(bid, record)
        return record

    def suggest_availability(self, *, service_ids: list[str], duration_min: int = 60) -> dict[str, Any]:
        try:
            employees = self.store.bos_employees.list_all() or None
            resources = self.store.bos_resources.list_all() or None
            result = self.library.availability.suggest(
                service_ids=service_ids,
                duration_min=duration_min,
                employees=employees,
                resources=resources,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        aid = _id("bcj_av")
        record = {"availability_id": aid, **result, "created_at": _now()}
        self.store.bcj_availability.save(aid, record)
        return record

    def smart_book(self, **kwargs: Any) -> dict[str, Any]:
        try:
            if kwargs.get("auto_pick") and not kwargs.get("suggestion"):
                avail = self.suggest_availability(
                    service_ids=kwargs.get("service_ids") or [],
                    duration_min=int(kwargs.get("duration_min", 60) or 60),
                )
                kwargs["suggestion"] = avail.get("optimal")
            booking = self.library.booking.book(**{k: v for k, v in kwargs.items() if k != "duration_min"})
        except TypeError as exc:
            raise ValidationError(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # Delegate persistence of appointment to Beauty OS when possible
        try:
            from applications.enterprise_hub import enterprise_hub

            appt = enterprise_hub.beauty_os.book_appointment(
                customer_id=booking["customer_id"],
                service_id=booking["service_ids"][0],
                employee_id=booking["employee_id"],
                branch_id=booking["branch_id"],
                start=booking["start"],
                end=booking["end"],
            )
            booking["appointment_id"] = appt.get("appointment_id")
        except Exception:
            booking["appointment_id"] = None
        bk = _id("bcj_bk")
        record = {"booking_id": bk, **booking, "created_at": _now()}
        self.store.bcj_bookings.save(bk, record)
        # Update or create journey
        journeys = [j for j in self.store.bcj_journeys.list_all() if j.get("customer_id") == booking["customer_id"]]
        if journeys:
            journey = self.library.journey.record_event(journeys[-1], kind="booking", payload=record)
            self.store.bcj_journeys.save(journeys[-1]["journey_id"], {**journey, "updated_at": _now()})
        else:
            journey = self.library.journey.create(customer_id=booking["customer_id"])
            journey = self.library.journey.record_event(journey, kind="booking", payload=record)
            jid = _id("bcj_jrn")
            self.store.bcj_journeys.save(jid, {"journey_id": jid, **journey, "created_at": _now()})
        for rem in self.library.reminders.seed_for_booking(
            customer_id=booking["customer_id"],
            appointment_id=booking.get("appointment_id") or bk,
        ):
            rid = _id("bcj_rem")
            self.store.bcj_reminders.save(rid, {"reminder_id": rid, **rem, "created_at": _now()})
        return record

    def create_journey(self, *, customer_id: str, source: str = "organic") -> dict[str, Any]:
        try:
            journey = self.library.journey.create(customer_id=customer_id, source=source)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        jid = _id("bcj_jrn")
        record = {"journey_id": jid, **journey, "created_at": _now()}
        self.store.bcj_journeys.save(jid, record)
        return record

    def join_waitlist(self, *, customer_id: str, service_ids: list[str], preferred_windows: list[str] | None = None) -> dict[str, Any]:
        try:
            entry = self.library.waitlist.join(
                customer_id=customer_id, service_ids=service_ids, preferred_windows=preferred_windows
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        wid = _id("bcj_wl")
        record = {"waitlist_id": wid, **entry, "created_at": _now()}
        self.store.bcj_waitlist.save(wid, record)
        return record

    def offer_waitlist_slot(self, *, customer_id: str, slot: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self.library.waitlist.offer_slot(customer_id=customer_id, slot=slot)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        oid = _id("bcj_off")
        record = {"offer_id": oid, **result, "offered_at": _now()}
        self.store.bcj_offers.save(oid, record)
        return record

    def loyalty_scan(self, *, journey_id: str) -> dict[str, Any]:
        journey = self.store.bcj_journeys.get(journey_id)
        if not journey:
            raise NotFoundError(f"journey not found: {journey_id}")
        result = self.library.loyalty.detect(journey)
        lid = _id("bcj_loy")
        record = {"loyalty_id": lid, "journey_id": journey_id, **result, "scanned_at": _now()}
        self.store.bcj_loyalty.save(lid, record)
        return record

    def booking_assistant(self, *, service_ids: list[str], customer_id: str = "") -> dict[str, Any]:
        avail = self.suggest_availability(service_ids=service_ids)
        journey = None
        if customer_id:
            matches = [j for j in self.store.bcj_journeys.list_all() if j.get("customer_id") == customer_id]
            journey = matches[-1] if matches else None
        result = self.library.assistant.recommend(availability=avail, journey=journey)
        asid = _id("bcj_ai")
        record = {"assistant_id": asid, **result, "created_at": _now()}
        self.store.bcj_assistant.save(asid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.bcj_bootstraps.list_all()),
            "journeys": len(self.store.bcj_journeys.list_all()),
            "bookings": len(self.store.bcj_bookings.list_all()),
            "waitlist": len(self.store.bcj_waitlist.list_all()),
            "reminders": len(self.store.bcj_reminders.list_all()),
        }


beauty_client_journey = BeautyClientJourneySuite()

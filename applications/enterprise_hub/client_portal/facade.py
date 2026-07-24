"""Client Portal Suite facade — Sprint 22.8 / v6.9.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_client_portal.facade import ClientPortalLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ClientPortalSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ClientPortalLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ClientPortalLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("cpl_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.cpl_bootstraps.save(bid, record)
        aid = _id("cpl_acc")
        self.store.cpl_accounts.save(aid, {"account_id": aid, **full["account"], "created_at": _now()})
        bkid = _id("cpl_bk")
        self.store.cpl_bookings.save(bkid, {"portal_booking_id": bkid, **full["booking"], "created_at": _now()})
        cid = _id("cpl_cal")
        self.store.cpl_calendars.save(cid, {"calendar_id": cid, **full["calendar"], "created_at": _now()})
        lid = _id("cpl_loy")
        self.store.cpl_loyalty.save(lid, {"loyalty_view_id": lid, **full["loyalty"], "created_at": _now()})
        asid = _id("cpl_ai")
        self.store.cpl_assistant.save(asid, {"assistant_id": asid, **full["assistant"], "created_at": _now()})
        nid = _id("cpl_ntf")
        self.store.cpl_notifications.save(nid, {"notification_id": nid, **full["notification"], "created_at": _now()})
        sid = _id("cpl_sec")
        self.store.cpl_security.save(sid, {"security_id": sid, **full["security"], "created_at": _now()})
        mid = _id("cpl_mob")
        self.store.cpl_mobile.save(mid, {"mobile_id": mid, **full["mobile"], "created_at": _now()})
        record["account_id"] = aid
        record["booking_id"] = bkid
        record["assistant_id"] = asid
        self.store.cpl_bootstraps.save(bid, record)
        return record

    def create_account(self, **kwargs: Any) -> dict[str, Any]:
        try:
            account = self.library.account.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # Enrich from commerce/beauty stores when available
        loyalty = [x for x in self.store.eco_loyalty.list_all() if x.get("customer_id") == kwargs.get("customer_id")]
        certs = [x for x in self.store.eco_certificates.list_all() if x.get("customer_id") == kwargs.get("customer_id")]
        mems = [x for x in self.store.eco_memberships.list_all() if x.get("customer_id") == kwargs.get("customer_id")]
        account = self.library.account.enrich(
            account,
            bonuses=(loyalty[-1].get("points") if loyalty else 0),
            certificates=certs,
            memberships=mems,
        )
        aid = _id("cpl_acc")
        record = {"account_id": aid, **account, "created_at": _now()}
        self.store.cpl_accounts.save(aid, record)
        return record

    def online_book(self, **kwargs: Any) -> dict[str, Any]:
        smart = None
        waitlist = bool(kwargs.get("waitlist", False))
        try:
            from applications.enterprise_hub import enterprise_hub

            if waitlist:
                enterprise_hub.beauty_client_journey.join_waitlist(
                    customer_id=kwargs.get("customer_id", ""),
                    service_ids=list(kwargs.get("service_ids") or []),
                )
            else:
                smart = enterprise_hub.beauty_client_journey.smart_book(
                    channel="online",
                    customer_id=kwargs.get("customer_id", ""),
                    service_ids=list(kwargs.get("service_ids") or []),
                    employee_id=kwargs.get("employee_id", ""),
                    branch_id=kwargs.get("branch_id", ""),
                    start=kwargs.get("start", ""),
                    end=kwargs.get("end", ""),
                    auto_pick=bool(kwargs.get("auto_pick", True)),
                )
        except Exception:
            smart = None
        try:
            booking = self.library.booking.book(
                customer_id=kwargs.get("customer_id", ""),
                branch_id=kwargs.get("branch_id", ""),
                service_ids=list(kwargs.get("service_ids") or []),
                employee_id=kwargs.get("employee_id", ""),
                start=kwargs.get("start", ""),
                end=kwargs.get("end", ""),
                waitlist=waitlist,
                smart_booking_result=smart,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        bkid = _id("cpl_bk")
        record = {"portal_booking_id": bkid, **booking, "created_at": _now()}
        self.store.cpl_bookings.save(bkid, record)
        # push confirmation via portal + communications hub when possible
        note = self.library.notifications.push(
            kind="booking_confirmation" if not waitlist else "salon_message",
            title="Booking update",
            customer_id=kwargs.get("customer_id", ""),
            body=booking.get("status", ""),
        )
        nid = _id("cpl_ntf")
        self.store.cpl_notifications.save(nid, {"notification_id": nid, **note, "created_at": _now()})
        try:
            from applications.enterprise_hub import enterprise_hub

            enterprise_hub.communications_hub.send_message(
                channel="push",
                recipient=kwargs.get("customer_id", ""),
                body=note["title"],
                approved=True,
                customer_id=kwargs.get("customer_id", ""),
                industry="beauty",
            )
        except Exception:
            pass
        return record

    def personal_calendar(self, *, customer_id: str) -> dict[str, Any]:
        appts = [
            a
            for a in self.store.bos_appointments.list_all()
            if a.get("customer_id") == customer_id
        ]
        portal_appts = [
            b for b in self.store.cpl_bookings.list_all() if b.get("customer_id") == customer_id
        ]
        merged = appts + portal_appts
        cal = self.library.calendar.render(appointments=merged, ai_recommendations=["rebook_soon"])
        cid = _id("cpl_cal")
        record = {"calendar_id": cid, "customer_id": customer_id, **cal, "created_at": _now()}
        self.store.cpl_calendars.save(cid, record)
        return record

    def loyalty_center(self, *, customer_id: str) -> dict[str, Any]:
        loyalty_rows = [x for x in self.store.eco_loyalty.list_all() if x.get("customer_id") == customer_id]
        loyalty = loyalty_rows[-1] if loyalty_rows else {"points": 0, "level": "new"}
        view = self.library.loyalty.view(loyalty=loyalty)
        lid = _id("cpl_loy")
        record = {"loyalty_view_id": lid, "customer_id": customer_id, **view, "created_at": _now()}
        self.store.cpl_loyalty.save(lid, record)
        return record

    def certificates(self, *, customer_id: str) -> dict[str, Any]:
        certs = [x for x in self.store.eco_certificates.list_all() if x.get("customer_id") == customer_id]
        view = self.library.certificates.list_certs(certs)
        return {"customer_id": customer_id, **view}

    def memberships(self, *, customer_id: str) -> dict[str, Any]:
        mems = [x for x in self.store.eco_memberships.list_all() if x.get("customer_id") == customer_id]
        view = self.library.memberships.view(mems)
        return {"customer_id": customer_id, **view}

    def assistant(self, *, customer_id: str) -> dict[str, Any]:
        accounts = [a for a in self.store.cpl_accounts.list_all() if a.get("customer_id") == customer_id]
        account = accounts[-1] if accounts else {"customer_id": customer_id}
        loyalty = self.loyalty_center(customer_id=customer_id)
        mems = [x for x in self.store.eco_memberships.list_all() if x.get("customer_id") == customer_id]
        result = self.library.assistant.recommend(account=account, loyalty=loyalty, memberships=mems)
        asid = _id("cpl_ai")
        record = {"assistant_id": asid, "customer_id": customer_id, **result, "created_at": _now()}
        self.store.cpl_assistant.save(asid, record)
        return record

    def notifications(self, *, customer_id: str) -> dict[str, Any]:
        stored = [n for n in self.store.cpl_notifications.list_all() if n.get("customer_id") == customer_id]
        if not stored:
            note = self.library.notifications.push(
                kind="reminder", title="Welcome", customer_id=customer_id, body="Your portal is ready"
            )
            nid = _id("cpl_ntf")
            self.store.cpl_notifications.save(nid, {"notification_id": nid, **note, "created_at": _now()})
            stored = [n for n in self.store.cpl_notifications.list_all() if n.get("customer_id") == customer_id]
        return {"customer_id": customer_id, "events": stored, "count": len(stored)}

    def secure_account(self, *, customer_id: str, device_id: str = "web", platform: str = "pwa") -> dict[str, Any]:
        try:
            twofa = self.library.security.enable_2fa(customer_id=customer_id)
            device = self.library.security.register_device(
                customer_id=customer_id, device_id=device_id, platform=platform
            )
            consent = self.library.security.consent(customer_id=customer_id, accepted=True)
            login = self.library.security.login_event(
                customer_id=customer_id, device_id=device_id, success=True
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("cpl_sec")
        record = {
            "security_id": sid,
            "two_factor": twofa,
            "device": device,
            "consent": consent,
            "login": login,
            "created_at": _now(),
        }
        self.store.cpl_security.save(sid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.cpl_bootstraps.list_all()),
            "accounts": len(self.store.cpl_accounts.list_all()),
            "bookings": len(self.store.cpl_bookings.list_all()),
            "notifications": len(self.store.cpl_notifications.list_all()),
        }


client_portal = ClientPortalSuite()

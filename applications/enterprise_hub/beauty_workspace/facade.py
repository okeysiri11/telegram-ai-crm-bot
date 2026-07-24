"""Beauty Workspace Suite facade — Sprint 22.3 / v6.4.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_beauty_workspace.facade import BeautyWorkspaceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BeautyWorkspaceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = BeautyWorkspaceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def _bos_context(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "appointments": self.store.bos_appointments.list_all(),
            "customers": self.store.bos_customers.list_all(),
            "employees": self.store.bos_employees.list_all(),
            "services": self.store.bos_services.list_all(),
        }

    def _advisor_recommendations(self) -> list[str]:
        briefs = self.store.aba_briefs.list_all()
        if not briefs:
            return []
        brief = briefs[-1]
        return list(brief.get("recommended_actions") or brief.get("ai_recommendations") or [])

    def bootstrap(self) -> dict[str, Any]:
        self.library = BeautyWorkspaceLibrary()
        # Prefer live Beauty OS data when present; otherwise seed via Beauty OS bootstrap.
        if not self.store.bos_appointments.list_all():
            try:
                from applications.enterprise_hub import enterprise_hub

                enterprise_hub.beauty_os.bootstrap()
            except Exception:
                pass
        result = self.library.bootstrap()
        full = result.pop("full")
        # Rebuild dashboard from live Beauty OS store when available
        ctx = self._bos_context()
        if ctx["appointments"] or ctx["employees"]:
            live_dash = self.library.reception.render(
                appointments=ctx["appointments"],
                employees=ctx["employees"] or [{"employee_id": "e0"}],
                open_slots=max(0, len(ctx["employees"]) * 8 - len(ctx["appointments"])),
                advisor_recommendations=self._advisor_recommendations() or full["dashboard"]["ai_recommendations"],
            )
            live_schedule = self.library.schedule.render(view="day", appointments=ctx["appointments"])
            full["dashboard"] = live_dash
            full["schedule"] = live_schedule
        bid = _id("bws_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.bws_bootstraps.save(bid, record)
        did = _id("bws_dash")
        self.store.bws_dashboards.save(did, {"dashboard_id": did, **full["dashboard"], "rendered_at": _now()})
        sid = _id("bws_sch")
        self.store.bws_schedules.save(sid, {"schedule_id": sid, **full["schedule"], "rendered_at": _now()})
        aid = _id("bws_ai")
        self.store.bws_assistant.save(aid, {"assistant_id": aid, **full["assistant"], "rendered_at": _now()})
        for note in full["notifications"]:
            nid = _id("bws_ntf")
            self.store.bws_notifications.save(nid, {"notification_id": nid, **note, "created_at": _now()})
        record["dashboard_id"] = did
        record["schedule_id"] = sid
        record["assistant_id"] = aid
        self.store.bws_bootstraps.save(bid, record)
        return record

    def reception_dashboard(self) -> dict[str, Any]:
        ctx = self._bos_context()
        dash = self.library.reception.render(
            appointments=ctx["appointments"],
            employees=ctx["employees"] or [{"employee_id": "e0"}],
            open_slots=max(0, len(ctx["employees"] or [1]) * 8 - len(ctx["appointments"])),
            advisor_recommendations=self._advisor_recommendations(),
        )
        did = _id("bws_dash")
        record = {"dashboard_id": did, **dash, "rendered_at": _now()}
        self.store.bws_dashboards.save(did, record)
        return record

    def schedule(self, *, view: str = "day") -> dict[str, Any]:
        try:
            result = self.library.schedule.render(view=view, appointments=self._bos_context()["appointments"])
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("bws_sch")
        record = {"schedule_id": sid, **result, "rendered_at": _now()}
        self.store.bws_schedules.save(sid, record)
        return record

    def move_appointment(
        self,
        *,
        appointment_id: str,
        start: str | None = None,
        end: str | None = None,
        employee_id: str | None = None,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        appt = self.store.bos_appointments.get(appointment_id)
        if not appt:
            raise NotFoundError(f"appointment not found: {appointment_id}")
        try:
            updated = self.library.schedule.move(
                appt,
                start=start,
                end=end,
                employee_id=employee_id,
                resource_id=resource_id,
                existing=self.store.bos_appointments.list_all(),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # Delegate status transition to Beauty OS when rescheduled
        if updated.get("status") == "rescheduled" and appt.get("status") in ("booked", "confirmed"):
            try:
                from applications.enterprise_hub import enterprise_hub

                enterprise_hub.beauty_os.transition_appointment(
                    appointment_id=appointment_id, status="rescheduled"
                )
                appt = self.store.bos_appointments.get(appointment_id) or appt
            except Exception:
                pass
        merged = {**appt, **updated, "updated_at": _now()}
        self.store.bos_appointments.save(appointment_id, merged)
        mid = _id("bws_mv")
        self.store.bws_moves.save(mid, {"move_id": mid, "appointment_id": appointment_id, **merged})
        self.library.notifications.publish(
            kind="reschedule",
            title=f"Appointment {appointment_id} moved",
            payload={"appointment_id": appointment_id},
        )
        return merged

    def panel_action(self, *, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            result = self.library.panel.invoke(action=action, payload=payload)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        pid = _id("bws_act")
        record = {"action_id": pid, **result, "invoked_at": _now()}
        self.store.bws_actions.save(pid, record)
        return record

    def quick_action(self, *, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            result = self.library.quick_actions.run(action=action, payload=payload)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        qid = _id("bws_qa")
        record = {"quick_action_id": qid, **result, "run_at": _now()}
        self.store.bws_quick_actions.save(qid, record)
        return record

    def search(self, *, query: str) -> dict[str, Any]:
        ctx = self._bos_context()
        try:
            result = self.library.search.search(
                query=query,
                customers=ctx["customers"],
                services=ctx["services"],
                employees=ctx["employees"],
                appointments=ctx["appointments"],
                certificates=self.store.bws_certificates.list_all(),
                memberships=self.store.bws_memberships.list_all(),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("bws_srch")
        record = {"search_id": sid, **result, "searched_at": _now()}
        self.store.bws_searches.save(sid, record)
        return record

    def notifications(self, *, unread_only: bool = False) -> dict[str, Any]:
        stored = self.store.bws_notifications.list_all()
        if not stored:
            for note in self.library.notifications.seed_defaults():
                nid = _id("bws_ntf")
                self.store.bws_notifications.save(nid, {"notification_id": nid, **note, "created_at": _now()})
            stored = self.store.bws_notifications.list_all()
        events = [e for e in stored if (not unread_only or not e.get("read"))]
        return {"events": events, "count": len(events)}

    def assistant(self) -> dict[str, Any]:
        recs = self._advisor_recommendations()
        panel = self.library.assistant.render(
            open_slots=["14:00", "16:30"],
            recommendations=recs or ["send_newsletter"],
            warnings=["check waiting queue"],
            overloaded_masters=[],
            churn_risks=[],
            promo_ideas=["loyalty_program"],
        )
        aid = _id("bws_ai")
        record = {"assistant_id": aid, **panel, "rendered_at": _now()}
        self.store.bws_assistant.save(aid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.bws_bootstraps.list_all()),
            "dashboards": len(self.store.bws_dashboards.list_all()),
            "schedules": len(self.store.bws_schedules.list_all()),
            "notifications": len(self.store.bws_notifications.list_all()),
            "searches": len(self.store.bws_searches.list_all()),
        }


beauty_workspace = BeautyWorkspaceSuite()

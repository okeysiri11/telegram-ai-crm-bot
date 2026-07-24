"""Beauty OS Suite facade — Sprint 22.2 / v6.3.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_beauty_os.facade import BeautyOSLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BeautyOSSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = BeautyOSLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = BeautyOSLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("bos_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.bos_bootstraps.save(bid, record)
        cid = _id("bos_co")
        self.store.bos_companies.save(cid, {"company_id": cid, **full["company"], "created_at": _now()})
        brid = _id("bos_br")
        self.store.bos_branches.save(brid, {"branch_id": brid, **full["branch"], "created_at": _now()})
        eid = _id("bos_em")
        self.store.bos_employees.save(eid, {"employee_id": eid, **full["employee"], "created_at": _now()})
        for svc in full["catalog"]:
            sid = _id("bos_svc")
            self.store.bos_services.save(sid, {"service_id": sid, **svc, "created_at": _now()})
        for res in full["resources"]:
            rid = _id("bos_res")
            self.store.bos_resources.save(rid, {"resource_id": rid, **res, "created_at": _now()})
        cuid = _id("bos_cu")
        self.store.bos_customers.save(cuid, {"customer_id": cuid, **full["customer"], "created_at": _now()})
        aid = _id("bos_ap")
        self.store.bos_appointments.save(aid, {"appointment_id": aid, **full["appointment"], "created_at": _now()})
        did = _id("bos_dash")
        self.store.bos_dashboards.save(did, {"dashboard_id": did, **full["dashboard"], "rendered_at": _now()})
        record["company_id"] = cid
        record["dashboard_id"] = did
        record["branch_id"] = brid
        self.store.bos_bootstraps.save(bid, record)
        return record

    def create_company(self, **kwargs: Any) -> dict[str, Any]:
        try:
            company = self.library.company.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cid = _id("bos_co")
        record = {"company_id": cid, **company, "created_at": _now()}
        self.store.bos_companies.save(cid, record)
        return record

    def create_branch(self, **kwargs: Any) -> dict[str, Any]:
        try:
            branch = self.library.branches.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        brid = _id("bos_br")
        record = {"branch_id": brid, **branch, "created_at": _now()}
        self.store.bos_branches.save(brid, record)
        return record

    def create_employee(self, **kwargs: Any) -> dict[str, Any]:
        try:
            employee = self.library.employees.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        eid = _id("bos_em")
        record = {"employee_id": eid, **employee, "created_at": _now()}
        self.store.bos_employees.save(eid, record)
        return record

    def create_service(self, **kwargs: Any) -> dict[str, Any]:
        try:
            service = self.library.services.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("bos_svc")
        record = {"service_id": sid, **service, "created_at": _now()}
        self.store.bos_services.save(sid, record)
        return record

    def create_customer(self, **kwargs: Any) -> dict[str, Any]:
        try:
            customer = self.library.customers.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cuid = _id("bos_cu")
        record = {"customer_id": cuid, **customer, "created_at": _now()}
        self.store.bos_customers.save(cuid, record)
        return record

    def book_appointment(self, **kwargs: Any) -> dict[str, Any]:
        try:
            appt = self.library.appointments.create(**kwargs)
            if kwargs.get("resource_id"):
                self.library.resources.book(
                    resource_id=kwargs["resource_id"],
                    start=kwargs["start"],
                    end=kwargs["end"],
                    appointment_id="pending",
                )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        aid = _id("bos_ap")
        record = {"appointment_id": aid, **appt, "created_at": _now()}
        self.store.bos_appointments.save(aid, record)
        return record

    def transition_appointment(self, *, appointment_id: str, status: str) -> dict[str, Any]:
        appt = self.store.bos_appointments.get(appointment_id)
        if not appt:
            raise NotFoundError(f"appointment not found: {appointment_id}")
        try:
            updated = self.library.appointments.transition(appt, status=status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.bos_appointments.save(appointment_id, {**updated, "updated_at": _now()})
        return updated

    def dashboard(self) -> dict[str, Any]:
        items = self.store.bos_dashboards.list_all()
        if items:
            return items[-1]
        advisor_brief = None
        try:
            from applications.enterprise_hub import enterprise_hub

            if enterprise_hub.store.aba_briefs.list_all():
                advisor_brief = enterprise_hub.store.aba_briefs.list_all()[-1]
            else:
                daily = enterprise_hub.ai_business_advisor.run_daily(industry="beauty")
                advisor_brief = daily
        except Exception:
            advisor_brief = {"recommended_actions": []}
        dash = self.library.dashboard.render(
            appointments=self.store.bos_appointments.list_all(),
            customers=self.store.bos_customers.list_all(),
            employees=self.store.bos_employees.list_all(),
            services=self.store.bos_services.list_all(),
            advisor_brief=advisor_brief,
        )
        did = _id("bos_dash")
        record = {"dashboard_id": did, **dash, "rendered_at": _now()}
        self.store.bos_dashboards.save(did, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.bos_bootstraps.list_all()),
            "companies": len(self.store.bos_companies.list_all()),
            "branches": len(self.store.bos_branches.list_all()),
            "employees": len(self.store.bos_employees.list_all()),
            "services": len(self.store.bos_services.list_all()),
            "appointments": len(self.store.bos_appointments.list_all()),
            "dashboards": len(self.store.bos_dashboards.list_all()),
        }


beauty_os = BeautyOSSuite()

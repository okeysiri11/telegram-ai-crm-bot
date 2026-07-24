"""Commerce Core Suite facade — Sprint 22.7 / v6.8.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_commerce.facade import CommerceCoreLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommerceCoreSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = CommerceCoreLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = CommerceCoreLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eco_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eco_bootstraps.save(bid, record)
        sid = _id("eco_sale")
        self.store.eco_sales.save(sid, {"sale_id": sid, **full["sale"], "created_at": _now()})
        pid = _id("eco_pos")
        self.store.eco_pos.save(pid, {"pos_id": pid, **full["pos"], "opened_at": _now()})
        cid = _id("eco_cert")
        self.store.eco_certificates.save(cid, {"certificate_id": cid, **full["certificate"], "created_at": _now()})
        mid = _id("eco_mem")
        self.store.eco_memberships.save(mid, {"membership_id": mid, **full["membership"], "created_at": _now()})
        lid = _id("eco_loy")
        self.store.eco_loyalty.save(lid, {"loyalty_id": lid, **full["loyalty"], "created_at": _now()})
        iid = _id("eco_inv")
        self.store.eco_inventory.save(iid, {"inventory_id": iid, **full["inventory"], "created_at": _now()})
        payid = _id("eco_pay")
        self.store.eco_payments.save(payid, {"payment_id": payid, **full["payment"], "created_at": _now()})
        aid = _id("eco_adv")
        self.store.eco_advisor.save(aid, {"advisor_id": aid, **full["advice"], "created_at": _now()})
        record["sale_id"] = sid
        record["certificate_id"] = cid
        record["membership_id"] = mid
        record["advisor_id"] = aid
        self.store.eco_bootstraps.save(bid, record)
        return record

    def open_pos(self, *, cashier_id: str = "cashier", industry: str = "beauty") -> dict[str, Any]:
        pos = self.library.pos.session(cashier_id=cashier_id, industry=industry)
        pid = _id("eco_pos")
        record = {"pos_id": pid, **pos, "opened_at": _now()}
        self.store.eco_pos.save(pid, record)
        return record

    def create_sale(self, **kwargs: Any) -> dict[str, Any]:
        try:
            sale = self.library.sales.sell(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        inv = self.library.inventory.deduct(sale_lines=sale["lines"])
        sid = _id("eco_sale")
        record = {"sale_id": sid, **sale, "inventory": inv, "created_at": _now()}
        self.store.eco_sales.save(sid, record)
        iid = _id("eco_inv")
        self.store.eco_inventory.save(iid, {"inventory_id": iid, "sale_id": sid, **inv, "created_at": _now()})
        return record

    def refund_sale(self, *, sale_id: str, amount: float | None = None) -> dict[str, Any]:
        sale = self.store.eco_sales.get(sale_id)
        if not sale:
            raise NotFoundError(f"sale not found: {sale_id}")
        try:
            result = self.library.sales.refund(sale, amount=amount)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eco_ref")
        record = {"refund_id": rid, **result, "created_at": _now()}
        self.store.eco_refunds.save(rid, record)
        return record

    def issue_certificate(self, *, face_value: float, customer_id: str = "") -> dict[str, Any]:
        try:
            cert = self.library.certificates.issue(face_value=face_value, customer_id=customer_id)
            cert = self.library.certificates.activate(cert)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cid = _id("eco_cert")
        record = {"certificate_id": cid, **cert, "created_at": _now()}
        self.store.eco_certificates.save(cid, record)
        return record

    def redeem_certificate(self, *, certificate_id: str, amount: float) -> dict[str, Any]:
        cert = self.store.eco_certificates.get(certificate_id)
        if not cert:
            raise NotFoundError(f"certificate not found: {certificate_id}")
        try:
            updated = self.library.certificates.redeem(cert, amount=amount)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.eco_certificates.save(certificate_id, {**updated, "updated_at": _now()})
        return updated

    def create_membership(self, **kwargs: Any) -> dict[str, Any]:
        try:
            membership = self.library.memberships.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        mid = _id("eco_mem")
        record = {"membership_id": mid, **membership, "created_at": _now()}
        self.store.eco_memberships.save(mid, record)
        return record

    def loyalty_profile(self, *, customer_id: str, points: float = 0.0) -> dict[str, Any]:
        try:
            profile = self.library.loyalty.profile(customer_id=customer_id, points=points)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        lid = _id("eco_loy")
        record = {"loyalty_id": lid, **profile, "created_at": _now()}
        self.store.eco_loyalty.save(lid, record)
        return record

    def charge(self, **kwargs: Any) -> dict[str, Any]:
        try:
            payment = self.library.payments.charge(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        payid = _id("eco_pay")
        record = {"payment_id": payid, **payment, "created_at": _now()}
        self.store.eco_payments.save(payid, record)
        return record

    def advise(self) -> dict[str, Any]:
        sales = self.store.eco_sales.list_all()
        certs = self.store.eco_certificates.list_all()
        loyalty = self.store.eco_loyalty.list_all()[-1] if self.store.eco_loyalty.list_all() else None
        advice = self.library.advisor.analyze(sales=sales, certificates=certs, loyalty=loyalty)
        aid = _id("eco_adv")
        record = {"advisor_id": aid, **advice, "created_at": _now()}
        self.store.eco_advisor.save(aid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eco_bootstraps.list_all()),
            "sales": len(self.store.eco_sales.list_all()),
            "certificates": len(self.store.eco_certificates.list_all()),
            "memberships": len(self.store.eco_memberships.list_all()),
            "payments": len(self.store.eco_payments.list_all()),
        }


commerce_core = CommerceCoreSuite()

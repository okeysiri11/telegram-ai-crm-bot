"""Maintenance AI, ERP enterprise, analytics, integrations — Sprint 13.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["fleet", "service", "cost", "profit", "inventory", "executive"]
INTEGRATION_TARGETS = [
    "vin_intelligence",
    "inspection_ai",
    "dealer_crm",
    "buyer_ai",
    "seller_ai",
    "marketplace",
    "executive_dashboard",
    "ai_os",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MaintenanceAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def predict(
        self,
        *,
        vin: str,
        mileage: int = 50000,
        health_score: float = 80.0,
        recent_failures: int = 0,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        fail_prob = min(0.95, 0.1 + mileage / 200000.0 + recent_failures * 0.15 + max(0, (70 - health_score) / 100))
        downtime_days = round(1 + fail_prob * 5, 1)
        cost = round(200 + fail_prob * 1800 + mileage * 0.01, 2)
        recommendations = []
        if mileage >= 40000:
            recommendations.append("schedule_brake_inspection")
        if fail_prob > 0.4:
            recommendations.append("predictive_service_now")
        if health_score < 70:
            recommendations.append("full_diagnostics")
        rid = _id("erp_mai")
        result = {
            "prediction_id": rid,
            "vin": vin,
            "mileage": mileage,
            "failure_probability": round(fail_prob, 3),
            "repair_recommendations": recommendations or ["routine_check"],
            "maintenance_cost_forecast": cost,
            "vehicle_health_monitoring": {"score": health_score, "status": "watch" if health_score < 75 else "ok"},
            "downtime_prediction_days": downtime_days,
            "at": _now(),
        }
        return self.store.erp_maintenance_ai.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"predictions": self.store.erp_maintenance_ai.count()}


class EnterpriseERP:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_invoice(self, *, customer: str, amount: float, ref: str = "") -> dict[str, Any]:
        iid = _id("erp_inv")
        invoice = {
            "invoice_id": iid,
            "customer": customer,
            "amount": float(amount),
            "ref": ref,
            "status": "issued",
            "created_at": _now(),
        }
        return self.store.erp_invoices.save(iid, invoice)

    def create_contract(self, *, party: str, contract_type: str = "service", terms: dict[str, Any] | None = None) -> dict[str, Any]:
        cid = _id("erp_con")
        contract = {
            "contract_id": cid,
            "party": party,
            "contract_type": contract_type,
            "terms": terms or {},
            "status": "active",
            "created_at": _now(),
        }
        return self.store.erp_contracts.save(cid, contract)

    def procurement_request(self, *, title: str, budget: float = 0.0) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        pid = _id("erp_proc")
        req = {"procurement_id": pid, "title": title, "budget": float(budget), "status": "open", "created_at": _now()}
        return self.store.erp_procurement.save(pid, req)

    def portal_access(self, *, portal: str, principal: str) -> dict[str, Any]:
        if portal not in ("customer", "employee"):
            raise ValidationError("portal must be customer or employee")
        aid = _id("erp_portal")
        access = {
            "access_id": aid,
            "portal": portal,
            "principal": principal,
            "status": "granted",
            "at": _now(),
        }
        return self.store.erp_portals.save(aid, access)

    def status(self) -> dict[str, Any]:
        return {
            "invoices": self.store.erp_invoices.count(),
            "contracts": self.store.erp_contracts.count(),
            "procurement": self.store.erp_procurement.count(),
            "portal_access": self.store.erp_portals.count(),
        }


class ERPAnalytics:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def report(self, *, report_type: str = "fleet") -> dict[str, Any]:
        if report_type not in self.types:
            raise ValidationError(f"report_type must be one of {self.types}")
        if report_type == "fleet":
            metrics: dict[str, Any] = {
                "vehicles": self.store.erp_fleet_vehicles.count(),
                "trips": self.store.erp_trips.count(),
            }
        elif report_type == "service":
            metrics = {
                "service_orders": self.store.erp_service_orders.count(),
                "completed": len([o for o in self.store.erp_service_orders.list_all() if o.get("status") == "completed"]),
            }
        elif report_type == "cost":
            maint = self.store.erp_maintenance_ai.list_all()
            metrics = {"forecast_cost": round(sum(float(m.get("maintenance_cost_forecast") or 0) for m in maint), 2)}
        elif report_type == "profit":
            invoices = self.store.erp_invoices.list_all()
            metrics = {"invoice_revenue": round(sum(float(i.get("amount") or 0) for i in invoices), 2)}
        elif report_type == "inventory":
            metrics = {"parts": self.store.erp_parts.count(), "reservations": self.store.erp_part_reservations.count()}
        else:
            metrics = {
                "fleets": self.store.erp_fleets.count(),
                "service_orders": self.store.erp_service_orders.count(),
                "invoices": self.store.erp_invoices.count(),
                "predictions": self.store.erp_maintenance_ai.count(),
            }
        rid = _id("erp_an")
        report = {"report_id": rid, "report_type": report_type, "metrics": metrics, "generated_at": _now()}
        return self.store.erp_analytics.save(rid, report)

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.erp_analytics.count(), "types": self.types}


class ERPIntegrations:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.targets = list(INTEGRATION_TARGETS)

    def connect(self, *, target: str, endpoint: str = "") -> dict[str, Any]:
        if target not in self.targets:
            raise ValidationError(f"target must be one of {self.targets}")
        iid = _id("erp_int")
        record = {
            "integration_id": iid,
            "target": target,
            "endpoint": endpoint,
            "status": "connected",
            "connected_at": _now(),
        }
        return self.store.erp_integrations.save(iid, record)

    def list_connections(self) -> list[dict[str, Any]]:
        return [i for i in self.store.erp_integrations.list_all() if i.get("status") == "connected"]

    def status(self) -> dict[str, Any]:
        return {"connected": len(self.list_connections()), "targets": self.targets}

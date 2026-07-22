# Global Analytics Engine — executive KPIs across network / finance / ops.

from __future__ import annotations

from typing import Any

from applications.port_erp.shared.store import PortStore, port_store


class GlobalAnalyticsEngine:
    """Executive dashboard KPIs for the global port network."""

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def global_kpi(self) -> dict[str, Any]:
        return {
            "partners": self._store.network_partners.count(),
            "routes": self._store.network_routes.count(),
            "trade_lanes": self._store.trade_lanes.count(),
            "registry_entries": self._store.global_registry.count(),
            "integrations": self._store.integration_links.count(),
            "exchange_offers": self._store.exchange_offers.count(),
        }

    def port_kpi(self) -> dict[str, Any]:
        ports = [e for e in self._store.global_registry.list_all() if e.kind.value == "ports"]
        terminals = [e for e in self._store.global_registry.list_all() if e.kind.value == "terminals"]
        return {
            "registered_ports": len(ports) or self._store.ports.count(),
            "registered_terminals": len(terminals) or self._store.terminals.count(),
            "active_voyages": self._store.voyages.count(),
            "containers": self._store.containers.count(),
        }

    def financial_kpi(self) -> dict[str, Any]:
        invoices = self._store.commercial_invoices.list_all()
        payments = self._store.payments.list_all()
        revenue = sum(getattr(i, "total", 0) or 0 for i in invoices)
        collected = sum(getattr(p, "amount", 0) or 0 for p in payments)
        return {
            "invoice_count": len(invoices),
            "payment_count": len(payments),
            "revenue": revenue,
            "collected": collected,
            "outstanding": max(revenue - collected, 0),
        }

    def operational_kpi(self) -> dict[str, Any]:
        return {
            "gate_visits": self._store.gate_visits.count(),
            "yard_slots": self._store.yard_slots.count(),
            "equipment": self._store.equipment.count(),
            "customs_declarations": self._store.customs_declarations.count(),
            "transport_orders": self._store.transport_orders.count(),
            "containers": self._store.containers.count(),
        }

    def live_tracking_kpi(self) -> dict[str, Any]:
        return {
            "live_positions": self._store.live_positions.count(),
            "truck_tracks": self._store.truck_tracks.count(),
            "eta_predictions": self._store.eta_predictions.count(),
            "alerts": self._store.port_alerts.count(),
        }

    def risk_dashboard(self) -> dict[str, Any]:
        partners = self._store.network_partners.list_all()
        routes = self._store.network_routes.list_all()
        high_risk_partners = [p for p in partners if p.risk_score >= 0.6]
        high_risk_routes = [r for r in routes if r.risk_score >= 0.6]
        return {
            "high_risk_partners": len(high_risk_partners),
            "high_risk_routes": len(high_risk_routes),
            "partner_ids": [p.partner_id for p in high_risk_partners[:10]],
            "route_ids": [r.route_id for r in high_risk_routes[:10]],
        }

    def forecasts(self) -> dict[str, Any]:
        fin = self.financial_kpi()
        ops = self.operational_kpi()
        return {
            "forecast_revenue": round(fin["revenue"] * 1.08, 2),
            "forecast_throughput": ops["containers"] + ops["transport_orders"],
            "confidence": 0.72,
        }

    def executive_report(self) -> dict[str, Any]:
        return {
            "global": self.global_kpi(),
            "port": self.port_kpi(),
            "financial": self.financial_kpi(),
            "operational": self.operational_kpi(),
            "live_tracking": self.live_tracking_kpi(),
            "risk": self.risk_dashboard(),
            "forecasts": self.forecasts(),
        }


global_analytics_engine = GlobalAnalyticsEngine()

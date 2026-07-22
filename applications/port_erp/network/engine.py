# Network Engine — discovery, comparison, ETA, risk, trade recommendations.

from __future__ import annotations

from applications.port_erp.enterprise.models import NetworkRoute, TradeLane
from applications.port_erp.partners.engine import PartnerEngine, partner_engine
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class NetworkEngine:
    """Global port network services."""

    def __init__(
        self,
        store: PortStore | None = None,
        partners: PartnerEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._partners = partners or partner_engine

    def register_lane(self, lane: TradeLane) -> TradeLane:
        if not lane.origin_port or not lane.destination_port:
            raise ValidationError("origin_port and destination_port are required")
        return self._store.trade_lanes.save(lane.lane_id, lane)

    def list_lanes(self) -> list[TradeLane]:
        return self._store.trade_lanes.list_all()

    def register_route(self, route: NetworkRoute) -> NetworkRoute:
        if not route.origin or not route.destination:
            raise ValidationError("origin and destination are required")
        return self._store.network_routes.save(route.route_id, route)

    def get_route(self, route_id: str) -> NetworkRoute:
        route = self._store.network_routes.get(route_id)
        if route is None:
            raise NotFoundError("network_route", route_id)
        return route

    def list_routes(self) -> list[NetworkRoute]:
        return self._store.network_routes.list_all()

    def discover_partners(self, *, capability: str = "", region: str = ""):
        return self._partners.discover(capability=capability, region=region)

    def discover_routes(self, *, origin: str = "", destination: str = "") -> list[NetworkRoute]:
        routes = self.list_routes()
        if origin:
            routes = [r for r in routes if r.origin.lower() == origin.lower()]
        if destination:
            routes = [r for r in routes if r.destination.lower() == destination.lower()]
        return routes

    def recommend_carriers(self, *, origin: str, destination: str, limit: int = 5) -> list[dict]:
        routes = self.discover_routes(origin=origin, destination=destination)
        ranked = sorted(routes, key=lambda r: (r.price, r.risk_score, r.eta_hours))
        out = []
        for route in ranked[:limit]:
            partner = None
            if route.carrier_id:
                try:
                    partner = self._partners.get(route.carrier_id)
                except NotFoundError:
                    partner = None
            out.append(
                {
                    "route": route.to_dict(),
                    "carrier": partner.to_dict() if partner else None,
                    "score": round(100 - route.risk_score * 40 - min(route.price / 100, 30), 2),
                }
            )
        return out

    def compare_prices(self, *, origin: str, destination: str) -> list[dict]:
        routes = self.discover_routes(origin=origin, destination=destination)
        return sorted(
            [{"route_id": r.route_id, "carrier_id": r.carrier_id, "price": r.price, "currency": r.currency} for r in routes],
            key=lambda x: x["price"],
        )

    def compare_capacity(self, *, origin: str, destination: str) -> list[dict]:
        routes = self.discover_routes(origin=origin, destination=destination)
        return sorted(
            [{"route_id": r.route_id, "capacity_teu": r.capacity_teu, "mode": r.mode} for r in routes],
            key=lambda x: -x["capacity_teu"],
        )

    def optimize_eta(self, *, origin: str, destination: str) -> dict | None:
        routes = self.discover_routes(origin=origin, destination=destination)
        if not routes:
            return None
        best = min(routes, key=lambda r: r.eta_hours)
        return {"best_route": best.to_dict(), "eta_hours": best.eta_hours}

    def analyze_risk(self, *, origin: str = "", destination: str = "") -> dict:
        routes = self.discover_routes(origin=origin, destination=destination) if (origin or destination) else self.list_routes()
        partners = self._partners.list_partners()
        avg_route = sum(r.risk_score for r in routes) / len(routes) if routes else 0.0
        avg_partner = sum(p.risk_score for p in partners) / len(partners) if partners else 0.0
        return {
            "route_count": len(routes),
            "partner_count": len(partners),
            "average_route_risk": round(avg_route, 3),
            "average_partner_risk": round(avg_partner, 3),
            "level": "high" if avg_route > 0.6 else "medium" if avg_route > 0.3 else "low",
        }

    def trade_recommendations(self, *, region: str = "") -> list[dict]:
        lanes = self.list_lanes()
        if region:
            lanes = [
                l for l in lanes
                if region.lower() in l.origin_port.lower() or region.lower() in l.destination_port.lower() or region.lower() in l.name.lower()
            ]
        recs = []
        for lane in lanes:
            routes = self.discover_routes(origin=lane.origin_port, destination=lane.destination_port)
            best_price = min((r.price for r in routes), default=None)
            recs.append(
                {
                    "lane": lane.to_dict(),
                    "available_routes": len(routes),
                    "best_price": best_price,
                    "recommendation": "expand" if len(routes) < 2 else "maintain",
                }
            )
        return recs

    def metrics(self) -> dict:
        return {
            "partners": len(self._partners.list_partners()),
            "routes": len(self.list_routes()),
            "trade_lanes": len(self.list_lanes()),
        }


network_engine = NetworkEngine()

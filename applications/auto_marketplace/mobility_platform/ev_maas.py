"""EV ecosystem and MaaS services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

MAAS_TYPES = ["ride_share", "car_share", "corporate", "subscription", "short_rental", "long_lease"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EVEcosystem:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_ev(self, *, vin: str, model: str = "", battery_kwh: float = 60.0) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        eid = _id("mp_ev")
        ev = {
            "ev_id": eid,
            "vin": vin,
            "model": model,
            "battery_kwh": float(battery_kwh),
            "health_score": 95.0,
            "created_at": _now(),
        }
        return self.store.mp_evs.save(eid, ev)

    def battery_health(self, ev_id: str, *, soh_pct: float = 92.0, cycles: int = 200) -> dict[str, Any]:
        ev = self.store.mp_evs.get(ev_id)
        if ev is None:
            raise NotFoundError("ev", ev_id)
        bid = _id("mp_batt")
        reading = {
            "battery_id": bid,
            "ev_id": ev_id,
            "soh_pct": float(soh_pct),
            "cycles": int(cycles),
            "degradation_pct": round(max(0.0, 100 - soh_pct), 2),
            "at": _now(),
        }
        ev["health_score"] = float(soh_pct)
        self.store.mp_evs.save(ev_id, ev)
        return self.store.mp_battery.save(bid, reading)

    def register_charger(self, *, name: str, lat: float = 0.0, lon: float = 0.0, kw: float = 50.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("charger name required")
        cid = _id("mp_chg")
        station = {"charger_id": cid, "name": name, "lat": float(lat), "lon": float(lon), "kw": float(kw), "created_at": _now()}
        return self.store.mp_chargers.save(cid, station)

    def start_session(self, *, ev_id: str, charger_id: str, kwh_target: float = 20.0) -> dict[str, Any]:
        if self.store.mp_evs.get(ev_id) is None:
            raise NotFoundError("ev", ev_id)
        if self.store.mp_chargers.get(charger_id) is None:
            raise NotFoundError("charger", charger_id)
        sid = _id("mp_sess")
        session = {
            "session_id": sid,
            "ev_id": ev_id,
            "charger_id": charger_id,
            "kwh_target": float(kwh_target),
            "kwh_delivered": 0.0,
            "status": "charging",
            "started_at": _now(),
        }
        return self.store.mp_charge_sessions.save(sid, session)

    def end_session(self, session_id: str, *, kwh_delivered: float) -> dict[str, Any]:
        session = self.store.mp_charge_sessions.get(session_id)
        if session is None:
            raise NotFoundError("charge_session", session_id)
        session["kwh_delivered"] = float(kwh_delivered)
        session["status"] = "completed"
        session["ended_at"] = _now()
        return self.store.mp_charge_sessions.save(session_id, session)

    def range_prediction(self, *, ev_id: str, soc_pct: float = 70.0, temp_c: float = 20.0) -> dict[str, Any]:
        ev = self.store.mp_evs.get(ev_id)
        if ev is None:
            raise NotFoundError("ev", ev_id)
        usable = float(ev.get("battery_kwh") or 60) * (soc_pct / 100) * (float(ev.get("health_score") or 90) / 100)
        efficiency = 0.18 + max(0, (15 - temp_c)) * 0.002
        range_km = round(usable / efficiency, 1)
        rid = _id("mp_range")
        result = {
            "range_id": rid,
            "ev_id": ev_id,
            "soc_pct": float(soc_pct),
            "predicted_range_km": range_km,
            "temp_c": float(temp_c),
            "at": _now(),
        }
        return self.store.mp_range.save(rid, result)

    def charging_route(self, *, ev_id: str, origin: str, destination: str) -> dict[str, Any]:
        if self.store.mp_evs.get(ev_id) is None:
            raise NotFoundError("ev", ev_id)
        chargers = self.store.mp_chargers.list_all()[:3]
        rid = _id("mp_croute")
        plan = {
            "charging_route_id": rid,
            "ev_id": ev_id,
            "origin": origin,
            "destination": destination,
            "stops": [{"charger_id": c["charger_id"], "name": c["name"]} for c in chargers],
            "at": _now(),
        }
        return self.store.mp_charge_routes.save(rid, plan)

    def energy_analytics(self, ev_id: str) -> dict[str, Any]:
        sessions = [s for s in self.store.mp_charge_sessions.list_all() if s.get("ev_id") == ev_id]
        aid = _id("mp_energy")
        result = {
            "analytics_id": aid,
            "ev_id": ev_id,
            "sessions": len(sessions),
            "kwh_total": round(sum(float(s.get("kwh_delivered") or 0) for s in sessions), 2),
            "at": _now(),
        }
        return self.store.mp_energy.save(aid, result)

    def status(self) -> dict[str, Any]:
        return {
            "evs": self.store.mp_evs.count(),
            "chargers": self.store.mp_chargers.count(),
            "sessions": self.store.mp_charge_sessions.count(),
        }


class MaaSPlatform:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(MAAS_TYPES)

    def create_offering(self, *, name: str, service_type: str, region: str = "") -> dict[str, Any]:
        if service_type not in self.types:
            raise ValidationError(f"service_type must be one of {self.types}")
        if not name:
            raise ValidationError("name required")
        oid = _id("mp_maas")
        offering = {
            "offering_id": oid,
            "name": name,
            "service_type": service_type,
            "region": region,
            "created_at": _now(),
        }
        return self.store.mp_maas_offerings.save(oid, offering)

    def reserve(self, *, offering_id: str, user: str, starts_at: str, ends_at: str = "") -> dict[str, Any]:
        if self.store.mp_maas_offerings.get(offering_id) is None:
            raise NotFoundError("maas_offering", offering_id)
        if not user:
            raise ValidationError("user required")
        rid = _id("mp_res")
        reservation = {
            "reservation_id": rid,
            "offering_id": offering_id,
            "user": user,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": "confirmed",
            "created_at": _now(),
        }
        return self.store.mp_maas_reservations.save(rid, reservation)

    def status(self) -> dict[str, Any]:
        return {
            "offerings": self.store.mp_maas_offerings.count(),
            "reservations": self.store.mp_maas_reservations.count(),
            "types": self.types,
        }

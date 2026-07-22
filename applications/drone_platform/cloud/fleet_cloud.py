"""Fleet Cloud — multi-company/country fleets, sharing, federation, global availability (Sprint 11.8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FleetCloud:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register_org_fleet(
        self,
        *,
        name: str,
        company_id: str,
        country: str = "UA",
        aircraft_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name or not company_id:
            raise ValidationError("name and company_id required")
        fid = f"cfleet_{uuid.uuid4().hex[:12]}"
        item = {
            "cloud_fleet_id": fid,
            "name": name,
            "company_id": company_id,
            "country": country,
            "aircraft_ids": list(aircraft_ids or []),
            "shared_with": [],
            "federated_with": [],
            "availability": "available",
            "maintenance_remote": False,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.cloud_fleets.save(fid, item)
        return item

    def get(self, cloud_fleet_id: str) -> dict[str, Any]:
        item = self.store.cloud_fleets.get(cloud_fleet_id)
        if item is None:
            raise NotFoundError("cloud_fleet", cloud_fleet_id)
        return item

    def list_fleets(self, *, company_id: str | None = None, country: str | None = None) -> list[dict[str, Any]]:
        items = self.store.cloud_fleets.list_all()
        if company_id:
            items = [i for i in items if i.get("company_id") == company_id]
        if country:
            items = [i for i in items if i.get("country") == country]
        return items

    def share_fleet(self, cloud_fleet_id: str, *, with_company_id: str) -> dict[str, Any]:
        fleet = self.get(cloud_fleet_id)
        if with_company_id and with_company_id not in fleet["shared_with"]:
            fleet["shared_with"].append(with_company_id)
            self.store.cloud_fleets.save(cloud_fleet_id, fleet)
        return fleet

    def federate(self, cloud_fleet_id: str, *, peer_fleet_id: str) -> dict[str, Any]:
        fleet = self.get(cloud_fleet_id)
        self.get(peer_fleet_id)
        if peer_fleet_id not in fleet["federated_with"]:
            fleet["federated_with"].append(peer_fleet_id)
            self.store.cloud_fleets.save(cloud_fleet_id, fleet)
        return fleet

    def global_dashboard(self) -> dict[str, Any]:
        fleets = self.list_fleets()
        countries = sorted({f.get("country", "") for f in fleets if f.get("country")})
        companies = sorted({f.get("company_id", "") for f in fleets if f.get("company_id")})
        available = sum(1 for f in fleets if f.get("availability") == "available")
        return {
            "fleet_count": len(fleets),
            "countries": countries,
            "companies": companies,
            "available": available,
            "shared": sum(1 for f in fleets if f.get("shared_with")),
            "federated": sum(1 for f in fleets if f.get("federated_with")),
        }

    def global_availability(self) -> dict[str, Any]:
        fleets = self.list_fleets()
        return {
            "available": [f["cloud_fleet_id"] for f in fleets if f.get("availability") == "available"],
            "busy": [f["cloud_fleet_id"] for f in fleets if f.get("availability") == "busy"],
            "maintenance": [f["cloud_fleet_id"] for f in fleets if f.get("availability") == "maintenance"],
        }

    def remote_assignment(self, cloud_fleet_id: str, *, operator_id: str, mission_id: str = "") -> dict[str, Any]:
        fleet = self.get(cloud_fleet_id)
        aid = f"cass_{uuid.uuid4().hex[:10]}"
        assignment = {
            "assignment_id": aid,
            "cloud_fleet_id": cloud_fleet_id,
            "operator_id": operator_id,
            "mission_id": mission_id,
            "company_id": fleet["company_id"],
            "status": "assigned",
            "at": _now(),
        }
        self.store.cloud_assignments.save(aid, assignment)
        fleet["availability"] = "busy"
        self.store.cloud_fleets.save(cloud_fleet_id, fleet)
        return assignment

    def remote_maintenance(self, cloud_fleet_id: str, *, notes: str = "", enable: bool = True) -> dict[str, Any]:
        fleet = self.get(cloud_fleet_id)
        fleet["maintenance_remote"] = enable
        fleet["availability"] = "maintenance" if enable else "available"
        fleet["maintenance_notes"] = notes
        self.store.cloud_fleets.save(cloud_fleet_id, fleet)
        return fleet

    def status(self) -> dict[str, Any]:
        return {"fleet_cloud": "1.0", "fleets": len(self.list_fleets()), "ready": True}


fleet_cloud = FleetCloud()

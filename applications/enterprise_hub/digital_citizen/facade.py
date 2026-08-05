"""Enterprise Digital Citizen suite — Sprint 29.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


@dataclass
class Citizen:
    id: str
    display_name: str
    email: str
    status: str = "active"
    presence: str = "offline"
    office_id: str | None = None
    city_building_id: str | None = None
    primary_org_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "displayName": self.display_name,
            "identity": {"email": self.email},
            "status": self.status,
            "presence": {
                "status": self.presence,
                "officeId": self.office_id,
                "cityBuildingId": self.city_building_id,
            },
            "primaryOrgId": self.primary_org_id,
        }


@dataclass
class Membership:
    id: str
    citizen_id: str
    org_id: str
    role: str
    active: bool = True
    manager_citizen_id: str | None = None
    business_profile_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "citizenId": self.citizen_id,
            "orgId": self.org_id,
            "role": self.role,
            "active": self.active,
            "managerCitizenId": self.manager_citizen_id,
            "businessProfileId": self.business_profile_id,
        }


class DigitalCitizenSuite:
    def __init__(self, store: Any | None = None) -> None:
        self.store = store
        self.citizens: dict[str, Citizen] = {}
        self.memberships: dict[str, Membership] = {}
        self._seeded = False

    def seed(self) -> None:
        if self._seeded:
            return
        self.citizens["cit_owner_demo"] = Citizen(
            id="cit_owner_demo",
            display_name="Owner Demo",
            email="owner@demo.corp",
            presence="online",
            office_id="hq_floor_1",
            city_building_id="hub",
            primary_org_id="org_demo_corp",
        )
        self.memberships["om_owner"] = Membership(
            id="om_owner",
            citizen_id="cit_owner_demo",
            org_id="org_demo_corp",
            role="owner",
            business_profile_id="biz_demo_corp",
        )
        self._seeded = True

    def bootstrap(self) -> dict[str, Any]:
        self.seed()
        return {"ok": True, "suite": "digital_citizen", "version": "29.1", **self.status()}

    def status(self) -> dict[str, Any]:
        return {
            "name": "digital_citizen",
            "version": "29.1",
            "citizens": len(self.citizens),
            "memberships": len(self.memberships),
            "ready": True,
        }

    def inventory(self) -> dict[str, Any]:
        self.seed()
        return {
            "version": "29.1",
            "citizens": [c.to_dict() for c in self.citizens.values()],
            "memberships": [m.to_dict() for m in self.memberships.values()],
            "endpoints": [
                "GET /health",
                "GET /citizens",
                "GET /memberships",
                "GET /presence",
                "POST /presence",
                "GET /city/:id",
                "GET /inventory",
            ],
        }

    def dashboard(self) -> dict[str, Any]:
        self.seed()
        return {"stats": self.status()}

    def set_presence(self, citizen_id: str, status: str) -> Citizen | None:
        c = self.citizens.get(citizen_id)
        if not c:
            return None
        c.presence = status
        return c

    def city_facade(self, citizen_id: str) -> dict[str, Any] | None:
        c = self.citizens.get(citizen_id)
        if not c:
            return None
        mem = next((m for m in self.memberships.values() if m.citizen_id == citizen_id and m.active), None)
        return {
            "citizenId": c.id,
            "displayName": c.display_name,
            "presence": c.presence,
            "role": mem.role if mem else None,
            "companyOrgId": c.primary_org_id,
            "companyBusinessProfileId": mem.business_profile_id if mem else None,
            "officeId": c.office_id,
            "cityBuildingId": c.city_building_id,
            "aiAssignmentIds": [],
        }


digital_citizen = DigitalCitizenSuite()

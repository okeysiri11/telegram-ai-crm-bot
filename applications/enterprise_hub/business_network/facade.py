"""Enterprise Business Network suite — Sprint 29.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


@dataclass
class BusinessProfile:
    id: str
    company_name: str
    category: str = "other"
    status: str = "active"
    verification_status: str = "unverified"
    trust_level: int = 50
    headquarters: str | None = None
    visibility: str = "partners"
    owner_org_id: str = "org_default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "companyName": self.company_name,
            "category": self.category,
            "status": self.status,
            "verificationStatus": self.verification_status,
            "trustLevel": self.trust_level,
            "headquarters": self.headquarters,
            "visibility": self.visibility,
            "ownerOrgId": self.owner_org_id,
            "metadata": self.metadata,
        }


@dataclass
class Relationship:
    id: str
    from_profile_id: str
    to_profile_id: str
    type: str
    state: str = "pending"
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fromProfileId": self.from_profile_id,
            "toProfileId": self.to_profile_id,
            "type": self.type,
            "state": self.state,
            "history": self.history,
        }


class BusinessGraphEngine:
    """Relationship storage · traversal · queries."""

    def __init__(self) -> None:
        self.profiles: dict[str, BusinessProfile] = {}
        self.relationships: dict[str, Relationship] = {}

    def upsert_profile(self, profile: BusinessProfile) -> BusinessProfile:
        self.profiles[profile.id] = profile
        return profile

    def create_relationship(
        self,
        from_profile_id: str,
        to_profile_id: str,
        rel_type: str,
    ) -> Relationship:
        rel = Relationship(
            id=_uid("rel"),
            from_profile_id=from_profile_id,
            to_profile_id=to_profile_id,
            type=rel_type,
            history=[{"action": "created", "type": rel_type}],
        )
        self.relationships[rel.id] = rel
        return rel

    def approve(self, relationship_id: str) -> Relationship | None:
        rel = self.relationships.get(relationship_id)
        if not rel:
            return None
        rel.state = "approved"
        rel.history.append({"action": "approved"})
        return rel

    def reject(self, relationship_id: str) -> Relationship | None:
        rel = self.relationships.get(relationship_id)
        if not rel:
            return None
        rel.state = "rejected"
        rel.history.append({"action": "rejected"})
        return rel

    def snapshot(self) -> dict[str, Any]:
        nodes = [
            {
                "id": p.id,
                "profileId": p.id,
                "label": p.company_name,
                "category": p.category,
                "trustLevel": p.trust_level,
            }
            for p in self.profiles.values()
        ]
        edges = [
            {
                "id": f"e_{r.id}",
                "relationshipId": r.id,
                "from": r.from_profile_id,
                "to": r.to_profile_id,
                "type": r.type,
                "state": r.state,
                "weight": 0.8 if r.state == "approved" else 0.2,
            }
            for r in self.relationships.values()
        ]
        return {"nodes": nodes, "edges": edges}

    def connections(self, profile_id: str) -> dict[str, Any]:
        snap = self.snapshot()
        edges = [e for e in snap["edges"] if e["from"] == profile_id or e["to"] == profile_id]
        ids = {profile_id}
        for e in edges:
            ids.add(e["from"])
            ids.add(e["to"])
        nodes = [n for n in snap["nodes"] if n["id"] in ids]
        return {"nodes": nodes, "edges": edges}

    def city_facade(self, profile_id: str) -> dict[str, Any] | None:
        p = self.profiles.get(profile_id)
        if not p:
            return None
        count = sum(
            1
            for r in self.relationships.values()
            if r.state == "approved"
            and (r.from_profile_id == profile_id or r.to_profile_id == profile_id)
        )
        return {
            "profileId": p.id,
            "companyName": p.company_name,
            "status": p.status,
            "trustLevel": p.trust_level,
            "relationshipCount": count,
            "headquarters": p.headquarters,
            "verificationStatus": p.verification_status,
            "reputationScore": min(100, int(p.trust_level * 0.7 + count * 3)),
        }


class BusinessNetworkSuite:
    """Enterprise Hub suite facade for EBN."""

    def __init__(self, store: Any | None = None) -> None:
        self.store = store
        self.graph = BusinessGraphEngine()
        self._seeded = False

    def bootstrap(self) -> dict[str, Any]:
        self.seed()
        return {"ok": True, "suite": "business_network", "version": "29.0", **self.status()}

    def seed(self) -> None:
        if self._seeded:
            return
        self.graph.upsert_profile(
            BusinessProfile(
                id="biz_demo_corp",
                company_name="Demo Corp",
                category="technology",
                verification_status="verified",
                trust_level=82,
                headquarters="Enterprise City · Hub Plaza",
                owner_org_id="org_demo_corp",
            )
        )
        self.graph.upsert_profile(
            BusinessProfile(
                id="biz_northwind",
                company_name="Northwind Partners",
                category="services",
                verification_status="verified",
                trust_level=74,
                owner_org_id="org_northwind",
            )
        )
        rel = self.graph.create_relationship(
            "biz_demo_corp", "biz_northwind", "strategic_partner"
        )
        self.graph.approve(rel.id)
        self._seeded = True

    def status(self) -> dict[str, Any]:
        return {
            "name": "business_network",
            "version": "29.0",
            "profiles": len(self.graph.profiles),
            "relationships": len(self.graph.relationships),
            "ready": True,
        }

    def inventory(self) -> dict[str, Any]:
        self.seed()
        return {
            "version": "29.0",
            "profiles": [p.to_dict() for p in self.graph.profiles.values()],
            "relationships": [r.to_dict() for r in self.graph.relationships.values()],
            "endpoints": [
                "GET /health",
                "GET /profiles",
                "GET /relationships",
                "POST /relationships",
                "POST /relationships/:id/approve",
                "GET /graph",
                "GET /city/:id",
                "GET /inventory",
            ],
        }

    def dashboard(self) -> dict[str, Any]:
        self.seed()
        return {"stats": self.status(), "graph": self.graph.snapshot()}


business_network = BusinessNetworkSuite()

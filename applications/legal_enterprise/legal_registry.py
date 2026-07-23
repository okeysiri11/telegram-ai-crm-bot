"""Legal Registry — entities, individuals, attorneys, judges, agencies, roles."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegalRegistry:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.roles = list(DEFAULT_CONFIG.legal_roles)

    def register_entity(
        self,
        *,
        name: str,
        entity_type: str = "corporation",
        jurisdiction: str = "",
        registration_no: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("entity name required")
        eid = _id("le_ent")
        return self.store.legal_entities.save(
            eid,
            {
                "entity_id": eid,
                "name": name,
                "entity_type": entity_type,
                "jurisdiction": jurisdiction,
                "registration_no": registration_no,
                "created_at": _now(),
            },
        )

    def register_individual(
        self,
        *,
        full_name: str,
        national_id: str = "",
        residency: str = "",
    ) -> dict[str, Any]:
        if not full_name:
            raise ValidationError("full_name required")
        iid = _id("le_ind")
        return self.store.individuals.save(
            iid,
            {
                "individual_id": iid,
                "full_name": full_name,
                "national_id": national_id,
                "residency": residency,
                "created_at": _now(),
            },
        )

    def register_attorney(
        self,
        *,
        full_name: str,
        bar_number: str,
        firm: str = "",
        specializations: list[str] | None = None,
    ) -> dict[str, Any]:
        if not full_name:
            raise ValidationError("full_name required")
        if not bar_number:
            raise ValidationError("bar_number required")
        aid = _id("le_att")
        return self.store.attorneys.save(
            aid,
            {
                "attorney_id": aid,
                "full_name": full_name,
                "bar_number": bar_number,
                "firm": firm,
                "specializations": specializations or [],
                "created_at": _now(),
            },
        )

    def register_judge(
        self,
        *,
        full_name: str,
        court_id: str = "",
        title: str = "Judge",
    ) -> dict[str, Any]:
        if not full_name:
            raise ValidationError("full_name required")
        jid = _id("le_jdg")
        return self.store.judges.save(
            jid,
            {
                "judge_id": jid,
                "full_name": full_name,
                "court_id": court_id,
                "title": title,
                "created_at": _now(),
            },
        )

    def register_agency(
        self,
        *,
        name: str,
        agency_type: str = "ministry",
        country: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("agency name required")
        gid = _id("le_agy")
        return self.store.agencies.save(
            gid,
            {
                "agency_id": gid,
                "name": name,
                "agency_type": agency_type,
                "country": country,
                "created_at": _now(),
            },
        )

    def register_role(
        self,
        *,
        role_code: str,
        label: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        code = role_code.lower().strip()
        if code not in self.roles:
            raise ValidationError(f"role_code must be one of {self.roles}")
        rid = _id("le_role")
        return self.store.legal_roles.save(
            rid,
            {
                "role_id": rid,
                "role_code": code,
                "label": label or code.replace("_", " ").title(),
                "description": description,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "legal_entities": self.store.legal_entities.count(),
            "individuals": self.store.individuals.count(),
            "attorneys": self.store.attorneys.count(),
            "judges": self.store.judges.count(),
            "agencies": self.store.agencies.count(),
            "legal_roles": self.store.legal_roles.count(),
        }

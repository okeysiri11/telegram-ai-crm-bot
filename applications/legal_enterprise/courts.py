"""Court Infrastructure — registry, hierarchy, jurisdictions, categories."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CourtInfrastructure:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.levels = list(DEFAULT_CONFIG.court_levels)

    def register_court(
        self,
        *,
        name: str,
        level: str,
        region: str = "",
        jurisdiction_code: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("court name required")
        lvl = level.lower().strip()
        if lvl not in self.levels:
            raise ValidationError(f"level must be one of {self.levels}")
        cid = _id("crt")
        return self.store.courts.save(
            cid,
            {
                "court_id": cid,
                "name": name,
                "level": lvl,
                "region": region,
                "jurisdiction_code": jurisdiction_code,
                "created_at": _now(),
            },
        )

    def register_regional(self, *, name: str, region: str, jurisdiction_code: str = "") -> dict[str, Any]:
        return self.register_court(
            name=name, level="regional", region=region, jurisdiction_code=jurisdiction_code
        )

    def register_appeal(self, *, name: str, region: str = "", jurisdiction_code: str = "") -> dict[str, Any]:
        return self.register_court(
            name=name, level="appeal", region=region, jurisdiction_code=jurisdiction_code
        )

    def register_supreme(self, *, name: str, jurisdiction_code: str = "national") -> dict[str, Any]:
        return self.register_court(
            name=name, level="supreme", region="national", jurisdiction_code=jurisdiction_code
        )

    def define_hierarchy(
        self,
        *,
        lower_court_id: str,
        higher_court_id: str,
        relation: str = "appeals_to",
    ) -> dict[str, Any]:
        if self.store.courts.get(lower_court_id) is None:
            raise NotFoundError("court", lower_court_id)
        if self.store.courts.get(higher_court_id) is None:
            raise NotFoundError("court", higher_court_id)
        hid = _id("crt_hier")
        return self.store.court_hierarchies.save(
            hid,
            {
                "hierarchy_id": hid,
                "lower_court_id": lower_court_id,
                "higher_court_id": higher_court_id,
                "relation": relation,
                "created_at": _now(),
            },
        )

    def register_jurisdiction(
        self,
        *,
        code: str,
        name: str,
        territory: str = "",
        court_id: str = "",
    ) -> dict[str, Any]:
        if not code:
            raise ValidationError("jurisdiction code required")
        if not name:
            raise ValidationError("jurisdiction name required")
        if court_id and self.store.courts.get(court_id) is None:
            raise NotFoundError("court", court_id)
        jid = _id("crt_jur")
        return self.store.jurisdictions.save(
            jid,
            {
                "jurisdiction_id": jid,
                "code": code,
                "name": name,
                "territory": territory,
                "court_id": court_id,
                "created_at": _now(),
            },
        )

    def register_case_category(
        self,
        *,
        code: str,
        name: str,
        description: str = "",
    ) -> dict[str, Any]:
        if not code:
            raise ValidationError("category code required")
        if not name:
            raise ValidationError("category name required")
        kid = _id("crt_cat")
        return self.store.case_categories.save(
            kid,
            {
                "category_id": kid,
                "code": code.lower().strip(),
                "name": name,
                "description": description,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        by_level = {lvl: 0 for lvl in self.levels}
        for court in self.store.courts.list_all():
            lvl = court.get("level")
            if lvl in by_level:
                by_level[lvl] += 1
        return {
            "courts": self.store.courts.count(),
            "by_level": by_level,
            "hierarchies": self.store.court_hierarchies.count(),
            "jurisdictions": self.store.jurisdictions.count(),
            "case_categories": self.store.case_categories.count(),
        }

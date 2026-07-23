"""Legislation Registry — codes, treaties, version history."""

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


_TYPE_STORE = {
    "constitution": "constitutions",
    "civil": "civil_codes",
    "commercial": "commercial_codes",
    "criminal": "criminal_codes",
    "administrative": "administrative_codes",
    "tax": "tax_codes",
    "labor": "labor_codes",
    "treaty": "treaties",
}


class LegislationRegistry:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.legislation_types)

    def _bucket(self, legislation_type: str) -> Any:
        attr = _TYPE_STORE.get(legislation_type)
        if attr is None:
            raise ValidationError(f"legislation_type must be one of {self.types}")
        return getattr(self.store, attr)

    def register(
        self,
        *,
        legislation_type: str,
        title: str,
        code: str = "",
        jurisdiction: str = "",
        enacted_on: str = "",
        articles: int = 0,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        lt = legislation_type.lower().strip()
        bucket = self._bucket(lt)
        lid = _id(f"leg_{lt[:3]}")
        record = {
            "legislation_id": lid,
            "legislation_type": lt,
            "title": title,
            "code": code,
            "jurisdiction": jurisdiction,
            "enacted_on": enacted_on,
            "articles": int(articles or 0),
            "version": "1.0",
            "created_at": _now(),
        }
        bucket.save(lid, record)
        self.record_version(
            legislation_id=lid,
            version="1.0",
            change_summary="initial registration",
            legislation_type=lt,
        )
        return record

    def register_constitution(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="constitution", **kwargs)

    def register_civil_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="civil", **kwargs)

    def register_commercial_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="commercial", **kwargs)

    def register_criminal_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="criminal", **kwargs)

    def register_administrative_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="administrative", **kwargs)

    def register_tax_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="tax", **kwargs)

    def register_labor_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="labor", **kwargs)

    def register_treaty(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(legislation_type="treaty", **kwargs)

    def record_version(
        self,
        *,
        legislation_id: str,
        version: str,
        change_summary: str = "",
        legislation_type: str = "",
    ) -> dict[str, Any]:
        if not legislation_id:
            raise ValidationError("legislation_id required")
        if not version:
            raise ValidationError("version required")
        vid = _id("leg_ver")
        return self.store.legislation_versions.save(
            vid,
            {
                "version_id": vid,
                "legislation_id": legislation_id,
                "legislation_type": legislation_type,
                "version": version,
                "change_summary": change_summary,
                "recorded_at": _now(),
            },
        )

    def get(self, *, legislation_type: str, legislation_id: str) -> dict[str, Any]:
        bucket = self._bucket(legislation_type.lower().strip())
        item = bucket.get(legislation_id)
        if item is None:
            raise NotFoundError("legislation", legislation_id)
        return item

    def status(self) -> dict[str, Any]:
        return {
            "constitutions": self.store.constitutions.count(),
            "civil_codes": self.store.civil_codes.count(),
            "commercial_codes": self.store.commercial_codes.count(),
            "criminal_codes": self.store.criminal_codes.count(),
            "administrative_codes": self.store.administrative_codes.count(),
            "tax_codes": self.store.tax_codes.count(),
            "labor_codes": self.store.labor_codes.count(),
            "treaties": self.store.treaties.count(),
            "versions": self.store.legislation_versions.count(),
        }

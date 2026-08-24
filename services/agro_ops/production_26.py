"""AGRO 2.6 — operational fields / crops / sowing / works / machinery / harvest / economics.

Extends AGRO 2.3 production. Additive only. No invented KPIs. Harvest → warehouse via 2.2.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from services.agro_ops.production import (
    COST_CATEGORIES,
    FIELD_STATUSES,
    WORK_STATUSES,
    WORK_TYPES,
    _num,
    _round4,
    _s,
)
from services.agro_ops.rbac import can, require

PROD26_VERSION = "AGRO_2_6"

OWNERSHIP_TYPES = [
    ("owned", "Собственность"),
    ("lease", "Аренда"),
    ("sublease", "Субаренда"),
]

SOWING_STATUSES = [
    ("plan", "План"),
    ("prep", "Подготовка"),
    ("in_progress", "В работе"),
    ("done", "Завершён"),
    ("cancelled", "Отменён"),
]

# Map sowing statuses onto field_work statuses where shared.
SOWING_TO_WORK = {
    "plan": "planned",
    "prep": "planned",
    "in_progress": "in_progress",
    "done": "done",
    "cancelled": "cancelled",
}
WORK_TO_SOWING = {v: k for k, v in SOWING_TO_WORK.items()}
WORK_TO_SOWING["planned"] = "plan"
WORK_TO_SOWING["overdue"] = "prep"

MACHINE_TYPES = [
    ("tractor", "Трактор"),
    ("combine", "Комбайн"),
    ("seeder", "Сеялка"),
    ("sprayer", "Опрыскиватель"),
    ("truck", "Грузовик"),
    ("trailer", "Прицеп"),
    ("other", "Другая техника"),
]

MACHINE_STATUSES = [
    ("working", "Работает"),
    ("idle", "Свободна"),
    ("on_field", "На поле"),
    ("repair", "В ремонте"),
    ("service", "ТО"),
    ("inactive", "Неактивна"),
]

WORK26_TYPES = [
    ("tillage", "Подготовка почвы"),
    ("sowing", "Посев"),
    ("fertilizer", "Внесение удобрений"),
    ("spraying", "Опрыскивание"),
    ("irrigation", "Полив"),
    ("harvest", "Уборка"),
    ("transport", "Перевозка"),
    ("other", "Другое"),
]

DEFAULT_AGRO_CROPS = [
    {"name": "Пшеница", "variety": "Одесская", "season": "озимая"},
    {"name": "Кукуруза", "variety": "Гибрид", "season": "яровые"},
    {"name": "Подсолнечник", "variety": "Гибрид", "season": "яровые"},
    {"name": "Ячмень", "variety": "Стандарт", "season": "яровые"},
    {"name": "Соя", "variety": "Стандарт", "season": "яровые"},
    {"name": "Рапс", "variety": "Озимый", "season": "озимая"},
]

FIELD_REGISTRY_KEYS = (
    "name", "title", "number", "area_ha", "region", "district", "locality",
    "lat", "lng", "coordinates", "cadastre", "owner", "ownership_type",
    "lease_start", "lease_until", "lease_cost", "status", "responsible",
    "notes", "previous_crop", "polygon", "is_demo", "archived_at",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _map_provider() -> dict[str, Any]:
    """Abstraction: external tiles only if env configured — never hardcode secrets."""
    provider = (os.environ.get("AGRO_MAP_PROVIDER") or "").strip().lower()
    key_set = bool((os.environ.get("AGRO_MAP_API_KEY") or "").strip())
    if provider in {"mapbox", "google", "osm_tiles"} and key_set:
        return {
            "id": provider,
            "mode": "external",
            "configured": True,
            "label_ru": "Внешняя карта",
            "has_api_key": True,
        }
    if provider == "osm" or provider == "openstreetmap":
        return {
            "id": "osm",
            "mode": "external_no_key",
            "configured": True,
            "label_ru": "OpenStreetMap",
            "has_api_key": False,
        }
    return {
        "id": "fallback_svg",
        "mode": "fallback",
        "configured": False,
        "label_ru": "Схема полей (без внешнего провайдера)",
        "has_api_key": False,
    }


class AgroOpsProduction26Mixin:
    """AGRO 2.6 operational workflows on top of 2.3 production."""

    # ------------------------------------------------------------------
    # Field registry (extends create / 360 / archive)
    # ------------------------------------------------------------------

    async def create_field(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        area = _num(body.get("area_ha") or body.get("area"))
        if not area:
            return {"ok": False, "error": "validation", "message_ru": "Укажите площадь поля, га"}
        ownership = str(body.get("ownership_type") or body.get("ownership") or "owned")
        if ownership not in dict(OWNERSHIP_TYPES):
            ownership = "owned"
        n = 1 + len(self._prod_scope(org, "agro_field", self._ws(body)))  # type: ignore[attr-defined]
        coords = body.get("coordinates")
        lat = _num(body.get("lat")) if body.get("lat") is not None else None
        lng = _num(body.get("lng")) if body.get("lng") is not None else None
        if isinstance(coords, dict):
            lat = lat if lat is not None else _num(coords.get("lat"))
            lng = lng if lng is not None else _num(coords.get("lng"))
        item = {
            "title": body.get("title") or body.get("name") or f"Поле {body.get('number') or n}",
            "name": body.get("name") or body.get("title") or f"Поле {body.get('number') or n}",
            "number": body.get("number") or str(n),
            "area_ha": area,
            "region": body.get("region"),
            "district": body.get("district") or body.get("rayon"),
            "locality": body.get("locality") or body.get("settlement"),
            "lat": lat,
            "lng": lng,
            "coordinates": {"lat": lat, "lng": lng} if lat is not None and lng is not None else None,
            "cadastre": body.get("cadastre"),
            "owner": body.get("owner"),
            "ownership_type": ownership,
            "lease_start": body.get("lease_start"),
            "lease_until": body.get("lease_until") or body.get("lease_end"),
            "lease_cost": _num(body.get("lease_cost")),
            "polygon": body.get("polygon") or [],
            "status": body.get("status") or "idle",
            "responsible": body.get("responsible") or body.get("responsible_employee"),
            "notes": body.get("notes"),
            "previous_crop": body.get("previous_crop"),
            "workspace_id": self._ws(body),  # type: ignore[attr-defined]
            "is_demo": bool(body.get("is_demo")),
        }
        return await self.create_entity(org, "agro_field", item, role)  # type: ignore[attr-defined]

    async def update_field(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update") or self._prod_write(role, "fields")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", item_id)  # type: ignore[attr-defined]
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        patch: dict[str, Any] = {}
        for k in FIELD_REGISTRY_KEYS:
            if k in body and k not in {"is_demo", "archived_at"}:
                patch[k] = body[k]
        if "area" in body and "area_ha" not in patch:
            patch["area_ha"] = _num(body.get("area"))
        if "ownership" in body and "ownership_type" not in patch:
            patch["ownership_type"] = body["ownership"]
        if "responsible_employee" in body:
            patch["responsible"] = body["responsible_employee"]
        if "lease_end" in body and "lease_until" not in patch:
            patch["lease_until"] = body["lease_end"]
        if "lat" in body or "lng" in body:
            lat = _num(body.get("lat")) if body.get("lat") is not None else field.get("lat")
            lng = _num(body.get("lng")) if body.get("lng") is not None else field.get("lng")
            patch["lat"] = lat
            patch["lng"] = lng
            patch["coordinates"] = {"lat": lat, "lng": lng} if lat is not None and lng is not None else None
        if "name" in patch and "title" not in patch:
            patch["title"] = patch["name"]
        return await self.update_entity(org, "agro_field", item_id, patch, role)  # type: ignore[attr-defined]

    async def archive_field(self, organization_id: str, item_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "archive") or require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return await self.archive_entity(org, "agro_field", item_id, role)  # type: ignore[attr-defined]

    async def field_360(self, organization_id: str, item_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        from services.agro_ops.production import AgroOpsProductionMixin

        base = await AgroOpsProductionMixin.field_360(self, organization_id, item_id, role, query)
        if not base.get("ok"):
            return base
        from services.agro_ops.service import _org

        org = _org(organization_id)
        field = self._prod_find(org, "agro_field", item_id)  # type: ignore[attr-defined]
        if not field:
            return base
        season = self._current_season(org, item_id)  # type: ignore[attr-defined]
        econ = self._field_economics(org, field, season, role)
        item = dict(base.get("item") or {})
        for k in FIELD_REGISTRY_KEYS:
            if k in field and k not in item:
                item[k] = field.get(k)
        item["ownership_ru"] = dict(OWNERSHIP_TYPES).get(str(field.get("ownership_type") or "owned"))
        item["current_crop"] = (season or {}).get("crop") or item.get("crop")
        item["previous_crop"] = field.get("previous_crop")
        item["economics"] = econ
        sowings = [w for w in self._prod_scope(org, "field_work") if str(w.get("field_id")) == item_id and str(w.get("work_type")) == "sowing"]  # type: ignore[attr-defined]
        base["item"] = item
        base["economics"] = econ
        base["sowings"] = sowings
        base["counts_sowings"] = len(sowings)
        base["production_version"] = PROD26_VERSION
        base["map_provider"] = _map_provider()
        return base

    def _field_economics(self, org: str, field: dict[str, Any], season: dict[str, Any] | None, role: str | None) -> dict[str, Any]:
        """Real costs / harvest only — never invent revenue."""
        show = can(role, "finance") or can(role, "margins")
        fid = str(field.get("id"))
        by_cat: dict[str, float] = {c: 0.0 for c, _ in COST_CATEGORIES}
        any_cost = False
        total = 0.0
        if show:
            for c in self._prod_scope(org, "field_cost"):  # type: ignore[attr-defined]
                if str(c.get("field_id")) != fid:
                    continue
                if season and c.get("season_id") and str(c.get("season_id")) != str(season.get("id")):
                    continue
                amt = _num(c.get("amount"))
                if amt is None:
                    continue
                any_cost = True
                total += amt
                cat = str(c.get("category") or "other")
                by_cat[cat] = by_cat.get(cat, 0.0) + amt
        harvests = [h for h in self._prod_scope(org, "harvest_actual") if str(h.get("field_id")) == fid]  # type: ignore[attr-defined]
        qty = sum(_num(h.get("actual_tonnes")) or 0 for h in harvests) or None
        area = _num(field.get("area_ha"))
        yld = _round4(qty / area) if qty and area else None
        # Estimated revenue only when price is known on harvest or linked sale
        est_rev = None
        act_rev = None
        for h in harvests:
            p = _num(h.get("price_per_t") or h.get("estimated_price"))
            t = _num(h.get("actual_tonnes"))
            if p is not None and t is not None:
                est_rev = (est_rev or 0) + p * t
            ar = _num(h.get("actual_revenue"))
            if ar is not None:
                act_rev = (act_rev or 0) + ar
        cost_total = round(total, 2) if any_cost else None
        margin = None
        pl = None
        rev = act_rev if act_rev is not None else est_rev
        if rev is not None and cost_total is not None:
            margin = round(rev - cost_total, 2)
            pl = margin
        return {
            "total_costs": cost_total,
            "seed_costs": round(by_cat.get("seed", 0), 2) if any_cost else None,
            "fertilizer_costs": round(by_cat.get("fertilizer", 0), 2) if any_cost else None,
            "plant_protection": round(by_cat.get("cpp", 0), 2) if any_cost else None,
            "fuel": round(by_cat.get("fuel", 0), 2) if any_cost else None,
            "machinery": round(by_cat.get("machinery", 0), 2) if any_cost else None,
            "labor": round(by_cat.get("labour", 0), 2) if any_cost else None,
            "logistics": round(by_cat.get("storage", 0) + by_cat.get("contracted", 0), 2) if any_cost else None,
            "other_costs": round(by_cat.get("other", 0) + by_cat.get("lease", 0), 2) if any_cost else None,
            "harvest_quantity": qty,
            "yield_t_ha": yld,
            "estimated_revenue": round(est_rev, 2) if est_rev is not None else None,
            "actual_revenue": round(act_rev, 2) if act_rev is not None else None,
            "gross_margin": margin,
            "profit_loss": pl,
            "empty_ru": None if any_cost or qty else "Нет данных",
            "can_finance": show,
        }

    async def field_map(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        from services.agro_ops.production import AgroOpsProductionMixin

        base = await AgroOpsProductionMixin.field_map(self, organization_id, role, query)
        if not base.get("ok"):
            return base
        provider = _map_provider()
        features = []
        for f in base.get("features") or []:
            row = dict(f)
            # Enrich from field record for markers
            from services.agro_ops.service import _org

            org = _org(organization_id)
            field = self._prod_find(org, "agro_field", str(f.get("id")))  # type: ignore[attr-defined]
            work = self._today_work(org, str(f.get("id"))) if field else None  # type: ignore[attr-defined]
            if field:
                row["lat"] = field.get("lat")
                row["lng"] = field.get("lng")
                row["responsible"] = field.get("responsible")
                row["today_work"] = (work or {}).get("title")
                row["status_ru"] = dict(FIELD_STATUSES).get(str(row.get("status") or "idle"), "Свободно")
                has_geo = field.get("lat") is not None and field.get("lng") is not None
                row["marker"] = {"lat": field.get("lat"), "lng": field.get("lng")} if has_geo else None
                row["representation"] = "geo_marker" if has_geo else "fallback_polygon"
            features.append(row)
        return {
            **base,
            "features": features,
            "map_provider": provider,
            "compact_card_fields": ["name", "area_ha", "crop", "status_ru", "today_work", "responsible"],
            "production_version": PROD26_VERSION,
        }

    # ------------------------------------------------------------------
    # Agronomic crop catalog
    # ------------------------------------------------------------------

    async def ensure_agro_crops(self, organization_id: str, role: str | None) -> dict[str, Any]:
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        existing = active_only(self._bag(org).get("agro_crop") or [])  # type: ignore[attr-defined]
        if existing:
            return {"ok": True, "items": existing, "seeded": False}
        created = []
        for c in DEFAULT_AGRO_CROPS:
            saved = await self.create_entity(  # type: ignore[attr-defined]
                org,
                "agro_crop",
                {
                    "title": c["name"],
                    "name": c["name"],
                    "variety": c.get("variety"),
                    "hybrid": c.get("variety"),
                    "producer": c.get("producer"),
                    "season": c.get("season"),
                    "expected_yield": None,
                    "actual_yield": None,
                    "moisture_target": None,
                    "quality_parameters": None,
                    "notes": None,
                    "status": "active",
                    "workspace_id": "agro",
                },
                role or "agro_director",
            )
            if saved.get("ok"):
                created.append(saved["item"])
        return {"ok": True, "items": created, "seeded": True}

    async def list_agro_crops(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        await self.ensure_agro_crops(organization_id, role)
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        rows = active_only(self._bag(org).get("agro_crop") or [])  # type: ignore[attr-defined]
        q = query or {}
        search = (q.get("q") or "").strip().lower()
        status = (q.get("status") or "").strip()
        if search:
            rows = [r for r in rows if search in _s(r.get("name")).lower() or search in _s(r.get("variety")).lower()]
        if status:
            rows = [r for r in rows if str(r.get("status") or "active") == status]
        return {"ok": True, "items": rows, "total": len(rows), "production_version": PROD26_VERSION}

    async def create_agro_crop(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        name = _s(body.get("name") or body.get("title"))
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название культуры"}
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "agro_crop",
            {
                "title": name,
                "name": name,
                "variety": body.get("variety") or body.get("hybrid"),
                "hybrid": body.get("hybrid") or body.get("variety"),
                "producer": body.get("producer"),
                "season": body.get("season"),
                "expected_yield": _num(body.get("expected_yield")),
                "actual_yield": _num(body.get("actual_yield")),
                "moisture_target": _num(body.get("moisture_target")),
                "quality_parameters": body.get("quality_parameters"),
                "notes": body.get("notes"),
                "status": body.get("status") or "active",
                "workspace_id": self._ws(body),  # type: ignore[attr-defined]
            },
            role,
        )

    async def update_agro_crop(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        keys = (
            "name", "title", "variety", "hybrid", "producer", "season",
            "expected_yield", "actual_yield", "moisture_target", "quality_parameters", "notes", "status",
        )
        patch = {k: body[k] for k in keys if k in body}
        return await self.update_entity(org, "agro_crop", item_id, patch, role)  # type: ignore[attr-defined]

    async def archive_agro_crop(self, organization_id: str, item_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "archive") or require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return await self.archive_entity(org, "agro_crop", item_id, role)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Sowing workflow
    # ------------------------------------------------------------------

    def _sowing_costs(self, body: dict[str, Any], area: float | None) -> dict[str, Any]:
        seed = _num(body.get("seed_cost")) or 0
        fuel = _num(body.get("fuel_cost")) or 0
        fert = _num(body.get("fertilizer_cost")) or 0
        ppp = _num(body.get("ppp_cost") or body.get("plant_protection_cost")) or 0
        other = _num(body.get("other_costs")) or 0
        total = seed + fuel + fert + ppp + other
        # Also accept explicit total
        if body.get("total_cost") is not None:
            total = _num(body.get("total_cost")) or total
        cost_ha = round(total / area, 2) if area and total else (None if not total else None)
        if area and (seed or fuel or fert or ppp or other or body.get("total_cost") is not None):
            cost_ha = round(total / area, 2) if area else None
        any_c = any(x is not None for x in (
            body.get("seed_cost"), body.get("fuel_cost"), body.get("fertilizer_cost"),
            body.get("ppp_cost"), body.get("plant_protection_cost"), body.get("other_costs"), body.get("total_cost"),
        ))
        return {
            "seed_cost": _num(body.get("seed_cost")),
            "fuel_cost": _num(body.get("fuel_cost")),
            "fertilizer_cost": _num(body.get("fertilizer_cost")),
            "plant_protection_cost": _num(body.get("ppp_cost") or body.get("plant_protection_cost")),
            "other_costs": _num(body.get("other_costs")),
            "total_operation_cost": round(total, 2) if any_c else None,
            "cost_per_hectare": cost_ha if any_c and area else None,
        }

    async def create_sowing(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))  # type: ignore[attr-defined]
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        area = _num(body.get("area") or body.get("area_ha")) or _num(field.get("area_ha"))
        crop = _s(body.get("crop") or body.get("crop_name")) or "Пшеница"
        variety = body.get("variety") or body.get("hybrid")
        season_year = body.get("season") or body.get("year") or _now().year
        # Ensure season
        season = self._current_season(org, str(field["id"]))  # type: ignore[attr-defined]
        if not season or str(season.get("crop")) != crop:
            season_res = await self.create_season(  # type: ignore[attr-defined]
                organization_id,
                {
                    "field_id": field["id"],
                    "crop": crop,
                    "year": season_year,
                    "planned_area": area,
                    "planned_seed_rate": _num(body.get("seed_rate")),
                    "workspace_id": self._ws(body),  # type: ignore[attr-defined]
                },
                role,
            )
            season = season_res.get("item") if season_res.get("ok") else season
        costs = self._sowing_costs(body, area)
        st = str(body.get("status") or "plan")
        if st not in dict(SOWING_STATUSES):
            st = "plan"
        work_status = SOWING_TO_WORK.get(st, "planned")
        title = body.get("title") or f"Посев {crop} / {field.get('name')}"
        item = {
            "title": title,
            "work_type": "sowing",
            "field_id": field["id"],
            "season_id": (season or {}).get("id"),
            "crop": crop,
            "crop_id": body.get("crop_id"),
            "variety": variety,
            "hybrid": variety,
            "season_label": str(season_year),
            "sowing_date": body.get("sowing_date") or body.get("date") or body.get("planned_at"),
            "planned_at": body.get("sowing_date") or body.get("date") or body.get("planned_at"),
            "area_ha": area,
            "seed_rate": _num(body.get("seed_rate")),
            "seed_quantity": _num(body.get("seed_quantity")),
            "fuel_consumption": _num(body.get("fuel_consumption")),
            "machine_id": body.get("machinery") or body.get("machine_id"),
            "operator": body.get("operator"),
            "fertilizers": body.get("fertilizers"),
            "plant_protection": body.get("plant_protection") or body.get("ppp"),
            "responsible": body.get("responsible") or body.get("responsible_employee"),
            "notes": body.get("notes"),
            "sowing_status": st,
            "status": work_status,
            "workspace_id": self._ws(body),  # type: ignore[attr-defined]
            **costs,
        }
        saved = await self.create_entity(org, "field_work", item, role)  # type: ignore[attr-defined]
        if saved.get("ok") and costs.get("total_operation_cost") is not None and can(role, "finance"):
            await self.add_field_cost(  # type: ignore[attr-defined]
                organization_id,
                {
                    "field_id": field["id"],
                    "season_id": (season or {}).get("id"),
                    "category": "seed",
                    "amount": costs["total_operation_cost"],
                    "title": f"Посев — {title}",
                    "work_id": saved["item"]["id"],
                    "source": "field_work",
                    "source_id": saved["item"]["id"],
                    "workspace_id": self._ws(body),  # type: ignore[attr-defined]
                },
                role,
            )
        return {**saved, "cost_per_hectare": costs.get("cost_per_hectare"), "total_operation_cost": costs.get("total_operation_cost")}

    async def list_sowings(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = [w for w in self._prod_scope(org, "field_work", q.get("workspace_id")) if str(w.get("work_type")) == "sowing"]  # type: ignore[attr-defined]
        if q.get("field_id"):
            rows = [r for r in rows if str(r.get("field_id")) == q["field_id"]]
        if q.get("status"):
            rows = [r for r in rows if str(r.get("sowing_status") or WORK_TO_SOWING.get(str(r.get("status")), r.get("status"))) == q["status"]]
        if q.get("crop"):
            crop_q = q["crop"].lower()
            rows = [r for r in rows if crop_q in _s(r.get("crop")).lower()]
        if q.get("q"):
            s = q["q"].lower()
            rows = [r for r in rows if s in _s(r.get("title")).lower() or s in _s(r.get("crop")).lower()]
        items = []
        for r in rows:
            field = self._prod_find(org, "agro_field", str(r.get("field_id") or ""))  # type: ignore[attr-defined]
            st = str(r.get("sowing_status") or WORK_TO_SOWING.get(str(r.get("status")), "plan"))
            items.append({
                **{k: r.get(k) for k in (
                    "id", "title", "field_id", "crop", "variety", "season_label", "sowing_date",
                    "area_ha", "seed_rate", "seed_quantity", "machine_id", "operator", "responsible",
                    "total_operation_cost", "cost_per_hectare", "notes", "status",
                )},
                "sowing_status": st,
                "status_ru": dict(SOWING_STATUSES).get(st, st),
                "field_name": (field or {}).get("name"),
            })
        return {"ok": True, "items": items, "total": len(items), "production_version": PROD26_VERSION}

    async def set_sowing_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        st = str(body.get("status") or body.get("sowing_status") or "")
        if st not in dict(SOWING_STATUSES):
            return {"ok": False, "error": "validation", "message_ru": "Неверный статус посева"}
        work_st = SOWING_TO_WORK[st]
        # prep stays planned on work lifecycle
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        work = self._prod_find(org, "field_work", item_id)  # type: ignore[attr-defined]
        if not work or str(work.get("work_type")) != "sowing":
            return {"ok": False, "error": "not_found", "message_ru": "Посев не найден"}
        if work_st == str(work.get("status")) or (st == "prep" and str(work.get("status")) == "planned"):
            return await self.update_entity(org, "field_work", item_id, {"sowing_status": st}, role)  # type: ignore[attr-defined]
        if work_st != str(work.get("status")):
            res = await self.set_work_status(organization_id, item_id, {**body, "status": work_st}, role)  # type: ignore[attr-defined]
            if not res.get("ok"):
                # Allow direct patch for plan↔prep
                if st in {"plan", "prep"} and str(work.get("status")) == "planned":
                    return await self.update_entity(org, "field_work", item_id, {"sowing_status": st}, role)  # type: ignore[attr-defined]
                return res
        return await self.update_entity(org, "field_work", item_id, {"sowing_status": st}, role)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Agricultural works list / enriched create
    # ------------------------------------------------------------------

    async def list_works(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = list(self._prod_scope(org, "field_work", q.get("workspace_id")))  # type: ignore[attr-defined]
        for key, attr in (("field_id", "field_id"), ("status", "status"), ("machine_id", "machine_id"), ("operation", "work_type"), ("work_type", "work_type")):
            if q.get(key):
                rows = [r for r in rows if str(r.get(attr)) == q[key]]
        if q.get("responsible"):
            rps = q["responsible"].lower()
            rows = [r for r in rows if rps in _s(r.get("responsible") or r.get("operator")).lower()]
        if q.get("date_from"):
            rows = [r for r in rows if str(r.get("planned_at") or "")[:10] >= q["date_from"][:10]]
        if q.get("date_to"):
            rows = [r for r in rows if str(r.get("planned_at") or "")[:10] <= q["date_to"][:10]]
        if q.get("q"):
            s = q["q"].lower()
            rows = [r for r in rows if s in _s(r.get("title")).lower()]
        type_labels = dict(WORK26_TYPES) | dict(WORK_TYPES)
        items = []
        for r in rows:
            field = self._prod_find(org, "agro_field", str(r.get("field_id") or ""))  # type: ignore[attr-defined]
            mach = self._prod_find(org, "machine", str(r.get("machine_id") or "")) if r.get("machine_id") else None  # type: ignore[attr-defined]
            items.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "field_id": r.get("field_id"),
                "field_name": (field or {}).get("name"),
                "operation": r.get("work_type"),
                "operation_ru": type_labels.get(str(r.get("work_type")), r.get("work_type")),
                "planned_at": r.get("planned_at"),
                "actual_start": r.get("actual_start"),
                "actual_end": r.get("actual_end"),
                "machine_id": r.get("machine_id"),
                "machine_name": (mach or {}).get("name") or (mach or {}).get("title"),
                "operator": r.get("operator") or r.get("responsible"),
                "materials": r.get("materials") or r.get("fertilizers"),
                "fuel": r.get("fuel_consumption") or r.get("fuel"),
                "cost": r.get("cost") or r.get("total_operation_cost"),
                "status": r.get("status"),
                "status_ru": dict(WORK_STATUSES).get(str(r.get("status") or "planned")),
                "comment": r.get("notes") or r.get("comment"),
            })
        return {"ok": True, "items": items, "total": len(items), "work_types": [{"id": i, "label_ru": l} for i, l in WORK26_TYPES], "production_version": PROD26_VERSION}

    async def create_work_order(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        """Create field work with 2.6 operation types and cost fields."""
        denied = require(role, "create") or self._prod_write(role, "fields")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))  # type: ignore[attr-defined]
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        wtype = str(body.get("operation") or body.get("work_type") or body.get("type") or "tillage")
        labels = dict(WORK26_TYPES) | dict(WORK_TYPES)
        if wtype not in labels:
            wtype = "other"
        planned = body.get("planned_date") or body.get("planned_at") or body.get("date")
        title = body.get("title") or f"{labels.get(wtype, wtype)} / {field.get('name')}"
        cost = _num(body.get("cost"))
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "field_work",
            {
                "title": title,
                "work_type": wtype,
                "field_id": field["id"],
                "season_id": body.get("season_id") or (self._current_season(org, str(field["id"])) or {}).get("id"),  # type: ignore[attr-defined]
                "machine_id": body.get("machinery") or body.get("machine_id"),
                "implement_id": body.get("implement_id"),
                "operator": body.get("employee") or body.get("operator"),
                "responsible": body.get("responsible") or body.get("responsible_employee"),
                "planned_at": planned,
                "actual_date": body.get("actual_date"),
                "materials": body.get("materials"),
                "fuel": _num(body.get("fuel") or body.get("fuel_consumption")),
                "fuel_consumption": _num(body.get("fuel") or body.get("fuel_consumption")),
                "cost": cost,
                "notes": body.get("comment") or body.get("notes"),
                "status": body.get("status") or "planned",
                "workspace_id": self._ws(body),  # type: ignore[attr-defined]
            },
            role,
        )
        if saved.get("ok") and planned and can(role, "tasks"):
            await self.create_entity(  # type: ignore[attr-defined]
                org,
                "calendar",
                {
                    "title": title,
                    "starts_at": planned,
                    "event_type": wtype,
                    "field_id": field["id"],
                    "work_id": saved["item"]["id"],
                    "machine_id": body.get("machine_id") or body.get("machinery"),
                    "owner": body.get("responsible") or body.get("operator"),
                },
                role,
            )
        if saved.get("ok") and cost is not None and can(role, "finance"):
            await self.add_field_cost(  # type: ignore[attr-defined]
                organization_id,
                {
                    "field_id": field["id"],
                    "category": "machinery" if body.get("machine_id") or body.get("machinery") else "other",
                    "amount": cost,
                    "title": title,
                    "work_id": saved["item"]["id"],
                    "source": "field_work",
                    "source_id": saved["item"]["id"],
                    "workspace_id": self._ws(body),  # type: ignore[attr-defined]
                },
                role,
            )
        return saved

    # ------------------------------------------------------------------
    # Machinery registry
    # ------------------------------------------------------------------

    async def create_machine(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "machines")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        mtype = str(body.get("type") or body.get("kind") or "tractor")
        if mtype not in dict(MACHINE_TYPES):
            mtype = "other"
        status = str(body.get("status") or "idle")
        if status not in dict(MACHINE_STATUSES):
            status = "idle"
        plate = _s(body.get("plate") or body.get("gosnomer") or body.get("name"))
        name = _s(body.get("name") or body.get("title")) or plate or body.get("model") or "Техника"
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "machine",
            {
                "title": name,
                "name": name,
                "plate": plate,
                "kind": mtype,
                "type": mtype,
                "brand": body.get("brand") or body.get("make"),
                "model": body.get("model"),
                "vin": body.get("vin") or body.get("serial"),
                "serial": body.get("serial") or body.get("vin"),
                "year": body.get("year"),
                "owner": body.get("owner"),
                "responsible": body.get("responsible") or body.get("responsible_employee") or body.get("operator"),
                "operator": body.get("operator"),
                "status": status,
                "engine_hours": _num(body.get("engine_hours") or body.get("mileage")) or 0,
                "mileage": _num(body.get("mileage")),
                "fuel_consumption": _num(body.get("fuel_consumption")),
                "last_service": body.get("last_service"),
                "next_service": body.get("next_service"),
                "notes": body.get("notes"),
                "workspace_id": self._ws(body),  # type: ignore[attr-defined]
            },
            role,
        )

    async def list_machines(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = list(self._prod_scope(org, "machine", q.get("workspace_id")))  # type: ignore[attr-defined]
        if q.get("status"):
            rows = [r for r in rows if str(r.get("status")) == q["status"]]
        if q.get("type"):
            rows = [r for r in rows if str(r.get("type") or r.get("kind")) == q["type"]]
        if q.get("q"):
            s = q["q"].lower()
            rows = [r for r in rows if s in _s(r.get("name")).lower() or s in _s(r.get("plate")).lower() or s in _s(r.get("model")).lower()]
        items = []
        for r in rows:
            st = str(r.get("status") or "idle")
            tp = str(r.get("type") or r.get("kind") or "other")
            items.append({
                **{k: r.get(k) for k in (
                    "id", "name", "title", "plate", "brand", "model", "vin", "year", "owner",
                    "responsible", "engine_hours", "mileage", "fuel_consumption", "last_service", "next_service", "notes",
                )},
                "type": tp,
                "type_ru": dict(MACHINE_TYPES).get(tp, tp),
                "status": st,
                "status_ru": dict(MACHINE_STATUSES).get(st, st),
                "needs_service": bool(r.get("next_service") and str(r.get("next_service"))[:10] <= _now().date().isoformat()) or st == "service",
            })
        return {
            "ok": True,
            "items": items,
            "total": len(items),
            "types": [{"id": i, "label_ru": l} for i, l in MACHINE_TYPES],
            "statuses": [{"id": i, "label_ru": l} for i, l in MACHINE_STATUSES],
            "production_version": PROD26_VERSION,
        }

    async def machine_360(self, organization_id: str, item_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        mach = self._prod_find(org, "machine", item_id)  # type: ignore[attr-defined]
        if not mach:
            return {"ok": False, "error": "not_found", "message_ru": "Техника не найдена"}
        works = [w for w in self._prod_scope(org, "field_work") if str(w.get("machine_id")) == item_id]  # type: ignore[attr-defined]
        maint = [m for m in active_only(self._bag(org).get("maintenance") or []) if str(m.get("machine_id")) == item_id]  # type: ignore[attr-defined]
        docs = [f for f in active_only(self._bag(org).get("file") or []) if str(f.get("entity_id")) == item_id or str(f.get("machine_id")) == item_id]  # type: ignore[attr-defined]
        st = str(mach.get("status") or "idle")
        tp = str(mach.get("type") or mach.get("kind") or "other")
        return {
            "ok": True,
            "item": {
                **mach,
                "type_ru": dict(MACHINE_TYPES).get(tp, tp),
                "status_ru": dict(MACHINE_STATUSES).get(st, st),
            },
            "works": works,
            "maintenance": maint,
            "documents": docs,
            "production_version": PROD26_VERSION,
        }

    async def update_machine(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update") or self._prod_write(role, "machines")  # type: ignore[attr-defined]
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        keys = (
            "name", "title", "plate", "brand", "model", "vin", "serial", "year", "owner",
            "responsible", "operator", "status", "type", "kind", "engine_hours", "mileage",
            "fuel_consumption", "last_service", "next_service", "notes",
        )
        patch = {k: body[k] for k in keys if k in body}
        if "type" in patch and "kind" not in patch:
            patch["kind"] = patch["type"]
        if "gosnomer" in body:
            patch["plate"] = body["gosnomer"]
        return await self.update_entity(org, "machine", item_id, patch, role)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Harvest list + enriched record
    # ------------------------------------------------------------------

    async def record_harvest(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        from services.agro_ops.production import AgroOpsProductionMixin

        # Enrich body then delegate for core create + season update
        field_id = str(body.get("field_id") or "")
        gross = _num(body.get("gross_weight") or body.get("gross"))
        net = _num(body.get("net_weight") or body.get("net") or body.get("actual_tonnes") or body.get("tonnes"))
        if net is None and gross is not None:
            impurity = _num(body.get("impurity")) or 0
            net = gross * (1 - impurity / 100.0) if impurity else gross
        enriched = {
            **body,
            "actual_tonnes": net if net is not None else body.get("actual_tonnes"),
            "tonnes": net if net is not None else body.get("tonnes"),
            "gross_weight": gross,
            "net_weight": net,
            "impurity": _num(body.get("impurity")),
            "warehouse_id": body.get("warehouse_id") or body.get("warehouse_destination"),
            "transport": body.get("transport") or body.get("truck") or body.get("machine_id"),
            "responsible": body.get("responsible") or body.get("responsible_employee"),
            "quality": body.get("quality"),
            "moisture": _num(body.get("moisture")),
            "crop": body.get("crop"),
            "estimated_price": _num(body.get("estimated_price") or body.get("price_per_t")),
            "price_per_t": _num(body.get("price_per_t") or body.get("estimated_price")),
            "actual_revenue": _num(body.get("actual_revenue")),
            "operational_cost": _num(body.get("operational_cost")),
        }
        saved = await AgroOpsProductionMixin.record_harvest(self, organization_id, enriched, role)
        if not saved.get("ok"):
            return saved
        item = saved.get("item") or {}
        # Patch extra fields onto harvest_actual
        from services.agro_ops.service import _org

        org = _org(organization_id)
        extra = {
            "gross_weight": gross,
            "net_weight": net,
            "impurity": enriched.get("impurity"),
            "warehouse_id": enriched.get("warehouse_id"),
            "transport": enriched.get("transport"),
            "responsible": enriched.get("responsible"),
            "crop": enriched.get("crop") or item.get("crop"),
            "estimated_price": enriched.get("estimated_price"),
            "price_per_t": enriched.get("price_per_t"),
            "actual_revenue": enriched.get("actual_revenue"),
            "operational_cost": enriched.get("operational_cost"),
        }
        # estimated value
        est = None
        if enriched.get("price_per_t") is not None and net is not None:
            est = round(enriched["price_per_t"] * net, 2)
            extra["estimated_value"] = est
        await self.update_entity(org, "harvest_actual", str(item["id"]), {k: v for k, v in extra.items() if v is not None}, role)  # type: ignore[attr-defined]
        item = {**item, **{k: v for k, v in extra.items() if v is not None}}
        # Auto link warehouse if requested
        if body.get("to_warehouse") or body.get("warehouse_destination"):
            wh = await self.harvest_to_warehouse(  # type: ignore[attr-defined]
                organization_id,
                {
                    "harvest_id": item["id"],
                    "warehouse_id": enriched.get("warehouse_id"),
                    "workspace_id": self._ws(body),  # type: ignore[attr-defined]
                },
                role,
            )
            return {**saved, "item": item, "estimated_value": est, "warehouse": wh, "yield_t_ha": saved.get("yield_t_ha")}
        return {**saved, "item": item, "estimated_value": est}

    async def list_harvests(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = list(self._prod_scope(org, "harvest_actual", q.get("workspace_id")))  # type: ignore[attr-defined]
        if q.get("field_id"):
            rows = [r for r in rows if str(r.get("field_id")) == q["field_id"]]
        if q.get("crop"):
            cq = q["crop"].lower()
            rows = [r for r in rows if cq in _s(r.get("crop")).lower()]
        if q.get("q"):
            s = q["q"].lower()
            rows = [r for r in rows if s in _s(r.get("title")).lower()]
        items = []
        total_t = 0.0
        for r in rows:
            field = self._prod_find(org, "agro_field", str(r.get("field_id") or ""))  # type: ignore[attr-defined]
            season = self._prod_find(org, "crop_season", str(r.get("season_id") or "")) if r.get("season_id") else None  # type: ignore[attr-defined]
            t = _num(r.get("actual_tonnes")) or 0
            total_t += t
            area = _num(r.get("area_harvested"))
            items.append({
                **{k: r.get(k) for k in (
                    "id", "title", "field_id", "harvested_at", "actual_tonnes", "area_harvested",
                    "moisture", "impurity", "quality", "yield_t_ha", "warehouse_id", "lot_id",
                    "operation_id", "transport", "responsible", "gross_weight", "net_weight",
                    "estimated_value", "operational_cost", "price_per_t",
                )},
                "crop": r.get("crop") or (season or {}).get("crop"),
                "field_name": (field or {}).get("name"),
                "linked_warehouse": bool(r.get("lot_id") or r.get("operation_id")),
            })
        return {
            "ok": True,
            "items": items,
            "total": len(items),
            "total_tonnes": round(total_t, 4) if items else None,
            "production_version": PROD26_VERSION,
        }

    # ------------------------------------------------------------------
    # Command Center KPIs (real records only)
    # ------------------------------------------------------------------

    async def production_kpis_26(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        fields = self._prod_scope(org, "agro_field")  # type: ignore[attr-defined]
        land = round(sum(_num(f.get("area_ha")) or 0 for f in fields), 2)
        active_statuses = {"planned", "sown", "vegetation", "harvest"}
        active_fields = 0
        for f in fields:
            season = self._current_season(org, str(f["id"]))  # type: ignore[attr-defined]
            st = str((season or {}).get("status") or f.get("status") or "idle")
            if st in active_statuses:
                active_fields += 1
        sowings = [w for w in self._prod_scope(org, "field_work") if str(w.get("work_type")) == "sowing"]  # type: ignore[attr-defined]
        sow_done = len([w for w in sowings if str(w.get("status")) == "done" or str(w.get("sowing_status")) == "done"])
        sow_progress = round(sow_done / len(sowings) * 100, 1) if sowings else None
        harvests = self._prod_scope(org, "harvest_actual")  # type: ignore[attr-defined]
        plans = self._prod_scope(org, "harvest_plan")  # type: ignore[attr-defined]
        harv_t = sum(_num(h.get("actual_tonnes")) or 0 for h in harvests)
        plan_t = sum(_num(p.get("planned_total_tonnes")) or 0 for p in plans)
        harv_progress = round(harv_t / plan_t * 100, 1) if plan_t else (100.0 if harvests and not plans else None)
        machines = self._prod_scope(org, "machine")  # type: ignore[attr-defined]
        mach_active = len([m for m in machines if str(m.get("status")) in {"working", "on_field"}])
        today = _now().date().isoformat()
        mach_service = len([
            m for m in machines
            if str(m.get("status")) in {"service", "repair"}
            or (m.get("next_service") and str(m.get("next_service"))[:10] <= today)
        ])
        open_wo = len([w for w in self._prod_scope(org, "field_work") if str(w.get("status")) in {"planned", "in_progress", "overdue"}])  # type: ignore[attr-defined]
        show = can(role, "finance") or can(role, "margins")
        cost_season = None
        if show:
            acc = 0.0
            any_c = False
            for c in self._prod_scope(org, "field_cost"):  # type: ignore[attr-defined]
                amt = _num(c.get("amount"))
                if amt is None:
                    continue
                any_c = True
                acc += amt
            cost_season = round(acc, 2) if any_c else None
        year = str(_now().year)
        harv_season = sum(
            _num(h.get("actual_tonnes")) or 0
            for h in harvests
            if year in str(h.get("harvested_at") or "") or not h.get("harvested_at")
        )
        metrics = [
            {"id": "fields_total", "label_ru": "Полей всего", "value": len(fields), "view": "fields"},
            {"id": "hectares_total", "label_ru": "Гектаров всего", "value": land, "view": "fields"},
            {"id": "fields_active", "label_ru": "Активных полей", "value": active_fields, "view": "fields", "filter": "active"},
            {"id": "sowing_progress", "label_ru": "Прогресс посева, %", "value": sow_progress, "view": "sowing"},
            {"id": "harvest_progress", "label_ru": "Прогресс уборки, %", "value": harv_progress, "view": "harvest"},
            {"id": "machinery_active", "label_ru": "Техника в работе", "value": mach_active, "view": "machinery", "filter": "active"},
            {"id": "machinery_service", "label_ru": "Требует ТО", "value": mach_service, "view": "machinery", "filter": "service"},
            {"id": "open_work_orders", "label_ru": "Открытые работы", "value": open_wo, "view": "works"},
            {"id": "cost_season", "label_ru": "Затраты сезона", "value": cost_season if show else None, "view": "fields", "finance": True},
            {"id": "harvest_season", "label_ru": "Урожай сезона, т", "value": round(harv_season, 4) if harvests else None, "view": "harvest"},
        ]
        return {"ok": True, "metrics": metrics, "version": PROD26_VERSION, "production_version": PROD26_VERSION}

    async def agronomist_today(self, organization_id: str, role: str | None) -> dict[str, Any]:
        from services.agro_ops.production import AgroOpsProductionMixin

        base = await AgroOpsProductionMixin.agronomist_today(self, organization_id, role)
        if not base.get("ok"):
            return base
        kpis = await self.production_kpis_26(organization_id, role)
        return {
            **base,
            "version": PROD26_VERSION,
            "kpis_26": kpis.get("metrics") or [],
            "production_version": PROD26_VERSION,
        }

    async def director_production(self, organization_id: str, role: str | None) -> dict[str, Any]:
        from services.agro_ops.production import AgroOpsProductionMixin

        base = await AgroOpsProductionMixin.director_production(self, organization_id, role)
        if not base.get("ok"):
            return base
        kpis = await self.production_kpis_26(organization_id, role)
        return {**base, "version": PROD26_VERSION, "kpis_26": kpis.get("metrics") or [], "production_version": PROD26_VERSION}

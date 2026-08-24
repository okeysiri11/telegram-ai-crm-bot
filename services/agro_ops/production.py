"""AGRO 2.3 — field production: land bank, works, materials, harvest, costs.

Extends agro_ops. Grain warehouse receipts reuse AGRO 2.2. No invented yield/cost/weather.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from services.agro_ops.finance import _dec
from services.agro_ops.rbac import can, normalize_role, require
from services.agro_ops.warehouses import _qty

PROD_VERSION = "AGRO_2_3"

FIELD_STATUSES = [
    ("idle", "Свободно"),
    ("planned", "Запланировано"),
    ("sown", "Посеяно"),
    ("vegetation", "Вегетация"),
    ("harvest", "Уборка"),
    ("closed", "Закрыто"),
]

WORK_TYPES = [
    ("sowing", "Посев"),
    ("fertilizer", "Удобрение"),
    ("spraying", "Опрыскивание"),
    ("harvest", "Уборка"),
    ("tillage", "Обработка почвы"),
    ("other", "Другое"),
]

WORK_STATUSES = [
    ("planned", "Запланировано"),
    ("in_progress", "В работе"),
    ("done", "Выполнено"),
    ("overdue", "Просрочено"),
    ("cancelled", "Отменено"),
]

WORK_TRANSITIONS = {
    "planned": {"in_progress", "cancelled", "overdue"},
    "in_progress": {"done", "cancelled", "overdue"},
    "overdue": {"in_progress", "done", "cancelled"},
    "done": set(),
    "cancelled": set(),
}

MATERIAL_CATEGORIES = [
    ("seed", "Семена"),
    ("fertilizer", "Удобрения"),
    ("cpp", "СЗР"),
    ("fuel", "Топливо"),
    ("other", "Прочее"),
]

MATERIAL_MOVES = ("RECEIPT", "ISSUE", "TRANSFER", "RETURN", "ADJUSTMENT")

COST_CATEGORIES = [
    ("seed", "Seeds"),
    ("fertilizer", "Fertilizer"),
    ("cpp", "Crop protection"),
    ("fuel", "Fuel"),
    ("machinery", "Machinery"),
    ("labour", "Operator labour"),
    ("contracted", "Contracted work"),
    ("repairs", "Repairs"),
    ("lease", "Lease"),
    ("irrigation", "Irrigation"),
    ("electricity", "Electricity"),
    ("storage", "Storage"),
    ("other", "Other"),
]

ISSUE_TYPES = [
    ("weeds", "Weeds"),
    ("disease", "Disease"),
    ("pests", "Pests"),
    ("flooding", "Flooding"),
    ("drought", "Drought"),
    ("frost", "Frost"),
    ("machinery", "Machinery problem"),
    ("input", "Input shortage"),
    ("other", "Other"),
]

CROP_COLORS = {
    "Пшеница": "#c9a227",
    "Кукуруза": "#d97706",
    "Подсолнечник": "#eab308",
    "Соя": "#65a30d",
    "Ячмень": "#92400e",
    "Рапс": "#a3e635",
}
STATUS_COLORS = {
    "idle": "#1a2740",
    "planned": "#3b82f6",
    "sown": "#22c55e",
    "vegetation": "#16a34a",
    "harvest": "#ca8a04",
    "closed": "#64748b",
}
WORK_COLORS = {
    "overdue": "#dc2626",
    "in_progress": "#2563eb",
    "done": "#16a34a",
    "planned": "#94a3b8",
    "cancelled": "#64748b",
}
WEATHER_COLORS = {"Low": "#1a7f4c", "Medium": "#c9a227", "High": "#c2410c"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _s(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round4(value: float) -> float:
    return round(value, 4)


def _nd(value: Any) -> Any:
    return value if value not in (None, "") else None


class AgroOpsProductionMixin:
    """Mixed into AgroOpsService."""

    def _prod_find(self, org: str, kind: str, item_id: str) -> dict[str, Any] | None:
        bag = self._bag(org)  # type: ignore[attr-defined]
        return next((x for x in bag.get(kind) or [] if str(x.get("id")) == str(item_id)), None)

    def _ws(self, body: dict[str, Any] | None = None) -> str:
        return _s((body or {}).get("workspace_id")) or "agro"

    def _prod_write(self, role: str | None, domain: str) -> dict[str, Any] | None:
        r = normalize_role(role)
        if r in {"agro_director", "platform_owner"}:
            return None
        if r in {"agro_viewer", "agro_observer"}:
            return require(role, "create")
        allowed = {
            "fields": {"agro_agronomist", "agro_manager"},
            "machines": {"agro_mechanic", "agro_agronomist", "agro_manager"},
            "materials": {"agro_agronomist", "agro_warehouse", "agro_manager"},
            "harvest": {"agro_agronomist", "agro_manager"},
            "costs": {"agro_accountant"},
            "maintenance": {"agro_mechanic"},
        }.get(domain, set())
        if r not in allowed:
            return {
                "ok": False,
                "error": "forbidden",
                "message_ru": f"Роль «{r}» не может изменять {domain}",
                "role": r,
            }
        return None

    def _prod_scope(self, org: str, kind: str, workspace_id: str | None = None) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        rows = active_only(self._bag(org).get(kind) or [])  # type: ignore[attr-defined]
        ws = workspace_id or "agro"
        return [r for r in rows if str(r.get("workspace_id") or "agro") == ws]

    def _manager_fields(self, role: str | None, actor: str | None, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if normalize_role(role) != "agro_manager" or not actor:
            return rows
        return [r for r in rows if _s(r.get("responsible")) in {actor, ""}]

    def _crop_color(self, crop: str | None) -> str:
        return CROP_COLORS.get(_s(crop), "#64748b") if crop else "#1a2740"

    def _material_balance(self, org: str, material_id: str) -> float:
        from services.agro_ops.service import active_only

        total = Decimal("0")
        for m in active_only(self._bag(org).get("material_movement") or []):  # type: ignore[attr-defined]
            if str(m.get("material_id")) != str(material_id):
                continue
            qty = _dec(m.get("quantity"))
            mt = str(m.get("movement_type") or "")
            if mt in {"RECEIPT", "RETURN"} or (mt == "ADJUSTMENT" and qty >= 0):
                total += abs(qty)
            else:
                total -= abs(qty)
        return _round4(float(total))

    async def _add_material_move(
        self,
        org: str,
        *,
        movement_type: str,
        quantity: float,
        material_id: str,
        role: str | None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra = extra or {}
        if movement_type not in MATERIAL_MOVES:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип движения материала"}
        if quantity <= 0 and movement_type != "ADJUSTMENT":
            return {"ok": False, "error": "validation", "message_ru": "Количество должно быть больше нуля"}
        if movement_type in {"ISSUE", "TRANSFER"}:
            avail = self._material_balance(org, material_id)
            if quantity - avail > 1e-6:
                return {"ok": False, "error": "validation", "message_ru": f"Недостаточно остатка: доступно {avail}"}
        key = extra.get("idempotency_key")
        if key:
            from services.agro_ops.service import active_only

            hit = next((x for x in active_only(self._bag(org).get("material_movement") or []) if str(x.get("idempotency_key") or "") == str(key)), None)  # type: ignore[attr-defined]
            if hit:
                return {"ok": True, "item": hit, "idempotent": True}
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "material_movement",
            {
                "title": extra.get("title") or f"{movement_type} {quantity}",
                "movement_type": movement_type,
                "quantity": quantity,
                "material_id": material_id,
                "warehouse_id": extra.get("warehouse_id"),
                "field_id": extra.get("field_id"),
                "season_id": extra.get("season_id"),
                "work_id": extra.get("work_id"),
                "unit_cost": extra.get("unit_cost"),
                "idempotency_key": key,
                "workspace_id": extra.get("workspace_id") or "agro",
                "counterparty_id": extra.get("counterparty_id"),
                "deal_id": extra.get("deal_id"),
                "contract_id": extra.get("contract_id"),
                "invoice_id": extra.get("invoice_id"),
                "payment_id": extra.get("payment_id"),
            },
            role,
        )
        if saved.get("ok"):
            mat = self._prod_find(org, "material", material_id)
            if mat:
                await self.update_entity(org, "material", material_id, {"quantity": self._material_balance(org, material_id)}, role)  # type: ignore[attr-defined]
        return saved

    def _field_metrics(self, org: str, field: dict[str, Any], season: dict[str, Any] | None, role: str | None) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        fid = str(field.get("id"))
        sid = str((season or {}).get("id") or "")
        bag = self._bag(org)  # type: ignore[attr-defined]
        area = _num(field.get("area_ha"))
        harvested_ha = 0.0
        tonnes = 0.0
        for h in active_only(bag.get("harvest_actual") or []):
            if str(h.get("field_id")) != fid:
                continue
            if sid and str(h.get("season_id") or "") not in {sid, ""}:
                continue
            harvested_ha += _num(h.get("area_harvested")) or 0
            tonnes += _num(h.get("actual_tonnes")) or 0
        sown_ha = _num((season or {}).get("actual_area")) or area
        denom_ha = harvested_ha or sown_ha
        seed_qty = 0.0
        for m in active_only(bag.get("material_movement") or []):
            if str(m.get("field_id")) != fid or str(m.get("movement_type")) != "ISSUE":
                continue
            if sid and str(m.get("season_id") or "") not in {sid, ""}:
                continue
            mat = self._prod_find(org, "material", str(m.get("material_id") or ""))
            if str((mat or {}).get("category")) == "seed":
                seed_qty += _qty(m.get("quantity"))
        seed_rate = _round4(seed_qty / sown_ha) if sown_ha and seed_qty else None
        yield_tha = _round4(tonnes / denom_ha) if denom_ha and tonnes else None
        total_cost = None
        if can(role, "finance") or can(role, "margins"):
            acc = 0.0
            any_c = False
            for c in active_only(bag.get("field_cost") or []):
                if str(c.get("field_id")) != fid:
                    continue
                if sid and str(c.get("season_id") or "") not in {sid, ""}:
                    continue
                amt = _num(c.get("amount"))
                if amt is None:
                    continue
                any_c = True
                acc += amt
            total_cost = round(acc, 2) if any_c else None
        cost_ha = round(total_cost / area, 2) if total_cost is not None and area else None
        cost_t = round(total_cost / tonnes, 2) if total_cost is not None and tonnes else None
        return {
            "area_ha": area,
            "sown_ha": sown_ha,
            "harvested_ha": harvested_ha or None,
            "seed_qty": seed_qty or None,
            "seed_rate_kg_ha": seed_rate,
            "harvest_tonnes": tonnes or None,
            "yield_t_ha": yield_tha,
            "total_cost": total_cost,
            "cost_ha": cost_ha,
            "cost_t": cost_t,
        }

    async def create_field(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        area = _num(body.get("area_ha") or body.get("area"))
        if not area:
            return {"ok": False, "error": "validation", "message_ru": "Укажите площадь поля, га"}
        n = 1 + len(self._prod_scope(org, "agro_field", self._ws(body)))
        item = {
            "title": body.get("title") or body.get("name") or f"Поле {body.get('number') or n}",
            "name": body.get("name") or body.get("title") or f"Поле {body.get('number') or n}",
            "number": body.get("number") or str(n),
            "area_ha": area,
            "cadastre": body.get("cadastre"),
            "region": body.get("region"),
            "polygon": body.get("polygon") or [],
            "status": body.get("status") or "idle",
            "responsible": body.get("responsible"),
            "lease_until": body.get("lease_until"),
            "workspace_id": self._ws(body),
            "is_demo": bool(body.get("is_demo")),
        }
        return await self.create_entity(org, "agro_field", item, role)  # type: ignore[attr-defined]

    async def list_fields(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = self._manager_fields(role, q.get("actor"), self._prod_scope(org, "agro_field", q.get("workspace_id")))
        search = (q.get("q") or "").strip().lower()
        if search:
            rows = [r for r in rows if search in _s(r.get("name")).lower() or search in _s(r.get("cadastre")).lower() or search in _s(r.get("number")).lower()]
        items = []
        for r in rows:
            season = self._current_season(org, str(r["id"]))
            today_work = self._today_work(org, str(r["id"]))
            wx = self._field_weather(org, r)
            items.append({
                "id": r.get("id"),
                "name": r.get("name") or r.get("title"),
                "number": r.get("number"),
                "area_ha": r.get("area_ha"),
                "crop": (season or {}).get("crop"),
                "status": (season or {}).get("status") or r.get("status"),
                "status_ru": dict(FIELD_STATUSES).get(str((season or {}).get("status") or r.get("status") or "idle"), "Свободно"),
                "today_work": (today_work or {}).get("title"),
                "today_at": (today_work or {}).get("planned_at"),
                "weather_risk": (wx or {}).get("label_ru") if wx else "Нет данных",
                "is_demo": bool(r.get("is_demo")),
            })
        return {"ok": True, "items": items, "total": len(items), "land_bank_ha": round(sum(_num(r.get("area_ha")) or 0 for r in rows), 2)}

    def _current_season(self, org: str, field_id: str) -> dict[str, Any] | None:
        rows = [s for s in self._prod_scope(org, "crop_season") if str(s.get("field_id")) == str(field_id)]
        rows.sort(key=lambda x: str(x.get("year") or x.get("created_at") or ""), reverse=True)
        return rows[0] if rows else None

    def _today_work(self, org: str, field_id: str) -> dict[str, Any] | None:
        today = _now().date().isoformat()
        for w in self._prod_scope(org, "field_work"):
            if str(w.get("field_id")) == str(field_id) and str(w.get("planned_at") or "")[:10] == today:
                return w
        return None

    def _field_weather(self, org: str, field: dict[str, Any]) -> dict[str, Any] | None:
        """Reuse stored weather observations — never invent."""
        from services.agro_ops.service import active_only

        region = _s(field.get("region")).lower()
        if not region:
            return None
        rows = active_only(self._bag(org).get("weather_observation") or [])  # type: ignore[attr-defined]
        hit = next((w for w in rows if region in _s(w.get("oblast") or w.get("region") or w.get("title")).lower()), None)
        if not hit:
            return None
        level = hit.get("risk_level") or (hit.get("agro_risk") or {}).get("level")
        return {"level": level, "label_ru": hit.get("risk_ru") or hit.get("label_ru") or ("Нет данных" if not level else str(level))}

    async def field_360(self, organization_id: str, item_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", item_id)
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        season = self._current_season(org, item_id)
        metrics = self._field_metrics(org, field, season, role)
        bag = self._bag(org)  # type: ignore[attr-defined]
        tab = (query or {}).get("tab") or "overview"
        linked = {
            "seasons": [s for s in active_only(bag.get("crop_season") or []) if str(s.get("field_id")) == item_id],
            "works": [w for w in active_only(bag.get("field_work") or []) if str(w.get("field_id")) == item_id],
            "materials": [m for m in active_only(bag.get("material_movement") or []) if str(m.get("field_id")) == item_id],
            "harvests": [h for h in active_only(bag.get("harvest_actual") or []) if str(h.get("field_id")) == item_id],
            "plans": [p for p in active_only(bag.get("harvest_plan") or []) if str(p.get("field_id")) == item_id],
            "costs": [c for c in active_only(bag.get("field_cost") or []) if str(c.get("field_id")) == item_id] if can(role, "finance") else [],
            "issues": [i for i in active_only(bag.get("field_issue") or []) if str(i.get("field_id")) == item_id],
            "documents": [f for f in active_only(bag.get("file") or []) if str(f.get("entity_id")) == item_id or str(f.get("field_id")) == item_id],
            "tasks": [t for t in active_only(bag.get("task") or []) if str(t.get("field_id")) == item_id],
        }
        rows = linked.get(tab) or []
        plan_vs = self._plan_vs_actual(org, field, season, metrics, role)
        return {
            "ok": True,
            "item": {
                **{k: field.get(k) for k in ("id", "name", "title", "number", "area_ha", "cadastre", "region", "status", "polygon", "lease_until", "responsible", "is_demo")},
                "crop": (season or {}).get("crop"),
                "season_id": (season or {}).get("id"),
                "season_year": (season or {}).get("year"),
                "status_ru": dict(FIELD_STATUSES).get(str((season or {}).get("status") or field.get("status") or "idle")),
                **metrics,
                "weather": self._field_weather(org, field) or {"label_ru": "Нет данных"},
            },
            "season": season,
            "plan_vs_actual": plan_vs,
            "tab": tab,
            "items": rows,
            "total": len(rows),
            "trace_forward": self._prod_trace(org, item_id, "forward"),
            "trace_back": self._prod_trace(org, item_id, "back"),
            "can_finance": can(role, "finance"),
            **{f"counts_{k}": len(v) for k, v in linked.items()},
        }

    def _plan_vs_actual(self, org: str, field: dict[str, Any], season: dict[str, Any] | None, metrics: dict[str, Any], role: str | None) -> dict[str, Any]:
        plan_area = _num((season or {}).get("planned_area")) or _num(field.get("area_ha"))
        plan_seed = _num((season or {}).get("planned_seed_rate"))
        plan_yield = _num((season or {}).get("planned_yield"))
        show_cost = can(role, "finance") or can(role, "margins")

        def row(plan: Any, actual: Any) -> dict[str, Any]:
            diff = None
            if plan is not None and actual is not None:
                diff = round(actual - plan, 4)
            return {"plan": plan, "actual": actual, "difference": diff}

        return {
            "area": row(plan_area, metrics.get("sown_ha")),
            "seed_rate": row(plan_seed, metrics.get("seed_rate_kg_ha")),
            "fertilizer": row(_num((season or {}).get("planned_fertilizer")), None),
            "crop_protection": row(_num((season or {}).get("planned_cpp")), None),
            "fuel": row(_num((season or {}).get("planned_fuel")), None),
            "machine_hours": row(_num((season or {}).get("planned_hours")), None),
            "yield": row(plan_yield, metrics.get("yield_t_ha")),
            "cost_ha": row(None, metrics.get("cost_ha") if show_cost else None),
            "cost_t": row(None, metrics.get("cost_t") if show_cost else None),
        }

    async def field_map(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        layer = q.get("layer") or "crop"
        fields = self._manager_fields(role, q.get("actor"), self._prod_scope(org, "agro_field", q.get("workspace_id")))
        features = []
        for i, f in enumerate(fields):
            season = self._current_season(org, str(f["id"]))
            metrics = self._field_metrics(org, f, season, role)
            work = self._today_work(org, str(f["id"]))
            wx = self._field_weather(org, f)
            st = str((season or {}).get("status") or f.get("status") or "idle")
            color = STATUS_COLORS.get(st, "#1a2740")
            if layer == "crop":
                color = self._crop_color((season or {}).get("crop"))
            elif layer == "work":
                wst = str((work or {}).get("status") or "planned") if work else "planned"
                color = WORK_COLORS.get(wst, "#94a3b8") if work else "#1a2740"
            elif layer == "weather":
                color = WEATHER_COLORS.get(str((wx or {}).get("level") or ""), "#1a2740")
            elif layer == "yield":
                y = metrics.get("yield_t_ha")
                color = "#1a2740" if y is None else ("#1a7f4c" if y >= 5 else "#c9a227" if y >= 3 else "#c2410c")
            elif layer == "cost":
                c = metrics.get("cost_ha")
                color = "#1a2740" if c is None else ("#c2410c" if c >= 25000 else "#c9a227" if c >= 15000 else "#1a7f4c")
            poly = f.get("polygon") or self._default_polygon(i)
            features.append({
                "id": f.get("id"),
                "name": f.get("name"),
                "area_ha": f.get("area_ha"),
                "crop": (season or {}).get("crop"),
                "status": st,
                "color": color,
                "polygon": poly,
                "yield_t_ha": metrics.get("yield_t_ha"),
                "cost_ha": metrics.get("cost_ha") if can(role, "finance") else None,
            })
        legend = self._map_legend(layer)
        return {"ok": True, "layer": layer, "features": features, "legend": legend}

    def _default_polygon(self, index: int) -> list[list[float]]:
        col, row = index % 6, index // 6
        x, y = 40 + col * 150, 40 + row * 110
        return [[x, y], [x + 120, y], [x + 120, y + 80], [x, y + 80]]

    def _map_legend(self, layer: str) -> list[dict[str, str]]:
        if layer == "crop":
            return [{"id": k, "label_ru": k, "color": v} for k, v in CROP_COLORS.items()] + [{"id": "other", "label_ru": "Другое / нет данных", "color": "#1a2740"}]
        if layer == "status" or layer == "field":
            return [{"id": i, "label_ru": l, "color": STATUS_COLORS[i]} for i, l in FIELD_STATUSES]
        if layer == "work":
            return [{"id": i, "label_ru": l, "color": WORK_COLORS.get(i, "#94a3b8")} for i, l in WORK_STATUSES]
        if layer == "weather":
            return [{"id": "Low", "label_ru": "Низкий риск", "color": "#1a7f4c"}, {"id": "Medium", "label_ru": "Средний", "color": "#c9a227"}, {"id": "High", "label_ru": "Высокий", "color": "#c2410c"}, {"id": "none", "label_ru": "Нет данных", "color": "#1a2740"}]
        if layer == "yield":
            return [{"id": "hi", "label_ru": "≥ 5 т/га", "color": "#1a7f4c"}, {"id": "mid", "label_ru": "3–5 т/га", "color": "#c9a227"}, {"id": "lo", "label_ru": "< 3 т/га", "color": "#c2410c"}, {"id": "none", "label_ru": "Нет данных", "color": "#1a2740"}]
        if layer == "cost":
            return [{"id": "hi", "label_ru": "≥ 25 000 /га", "color": "#c2410c"}, {"id": "mid", "label_ru": "15–25 тыс.", "color": "#c9a227"}, {"id": "lo", "label_ru": "< 15 000", "color": "#1a7f4c"}, {"id": "none", "label_ru": "Нет данных", "color": "#1a2740"}]
        return [{"id": i, "label_ru": l, "color": STATUS_COLORS[i]} for i, l in FIELD_STATUSES]

    async def create_season(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        crop = _s(body.get("crop") or "Пшеница")
        year = body.get("year") or _now().year
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "crop_season",
            {
                "title": f"{crop} {year} / {field.get('name')}",
                "field_id": field["id"],
                "crop": crop,
                "year": year,
                "planned_area": _num(body.get("planned_area")) or field.get("area_ha"),
                "planned_seed_rate": _num(body.get("planned_seed_rate")),
                "planned_yield": _num(body.get("planned_yield")),
                "status": body.get("status") or "planned",
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def create_work(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "fields")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        wtype = str(body.get("work_type") or body.get("type") or "sowing")
        planned = body.get("planned_at") or body.get("date")
        title = body.get("title") or f"{dict(WORK_TYPES).get(wtype, wtype)} / {field.get('name')}"
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "field_work",
            {
                "title": title,
                "work_type": wtype,
                "field_id": field["id"],
                "season_id": body.get("season_id") or (self._current_season(org, str(field["id"])) or {}).get("id"),
                "machine_id": body.get("machine_id"),
                "implement_id": body.get("implement_id"),
                "operator": body.get("operator"),
                "planned_at": planned,
                "planned_rate": _num(body.get("planned_rate")),
                "status": "planned",
                "workspace_id": self._ws(body),
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
                    "machine_id": body.get("machine_id"),
                    "owner": body.get("responsible") or body.get("operator"),
                },
                role,
            )
        return saved

    async def set_work_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        work = self._prod_find(org, "field_work", item_id)
        if not work:
            return {"ok": False, "error": "not_found", "message_ru": "Работа не найдена"}
        nxt = str(body.get("status") or "")
        cur = str(work.get("status") or "planned")
        if nxt == cur:
            return {"ok": True, "item": work}
        if nxt not in WORK_TRANSITIONS.get(cur, set()):
            return {"ok": False, "error": "validation", "message_ru": f"Нельзя перейти {cur} → {nxt}"}
        patch: dict[str, Any] = {"status": nxt}
        if nxt == "in_progress":
            patch["actual_start"] = body.get("actual_start") or _now().isoformat()
        if nxt == "done":
            patch["actual_end"] = body.get("actual_end") or _now().isoformat()
            patch["actual_qty"] = _num(body.get("actual_qty"))
            patch["hours"] = _num(body.get("hours"))
            if work.get("machine_id") and patch.get("hours"):
                mach = self._prod_find(org, "machine", str(work["machine_id"]))
                if mach:
                    hours = (_num(mach.get("engine_hours")) or 0) + (patch["hours"] or 0)
                    await self.update_entity(org, "machine", str(mach["id"]), {"engine_hours": hours}, role)  # type: ignore[attr-defined]
            if str(work.get("work_type")) == "sowing" and work.get("season_id"):
                season = self._prod_find(org, "crop_season", str(work["season_id"]))
                field = self._prod_find(org, "agro_field", str(work.get("field_id") or ""))
                if season:
                    await self.update_entity(org, "crop_season", str(season["id"]), {"status": "sown", "actual_area": _num(body.get("actual_area")) or (field or {}).get("area_ha")}, role)  # type: ignore[attr-defined]
        return await self.update_entity(org, "field_work", item_id, patch, role)  # type: ignore[attr-defined]

    async def create_machine(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "machines")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        plate = _s(body.get("plate") or body.get("name"))
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "machine",
            {
                "title": body.get("title") or plate or body.get("model") or "Машина",
                "name": plate or body.get("model"),
                "plate": plate,
                "kind": body.get("kind") or "tractor",
                "model": body.get("model"),
                "engine_hours": _num(body.get("engine_hours")) or 0,
                "operator": body.get("operator"),
                "status": body.get("status") or "idle",
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def create_implement(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "machines")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "implement",
            {
                "title": body.get("title") or body.get("name") or "Агрегат",
                "name": body.get("name") or body.get("title"),
                "kind": body.get("kind") or "seeder",
                "width": _num(body.get("width")),
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def create_material(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "materials")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "material",
            {
                "title": body.get("title") or body.get("name") or "Материал",
                "name": body.get("name") or body.get("title"),
                "category": body.get("category") or "other",
                "unit": body.get("unit") or "кг",
                "batch": body.get("batch"),
                "quantity": 0,
                "counterparty_id": body.get("counterparty_id"),
                "deal_id": body.get("deal_id"),
                "contract_id": body.get("contract_id"),
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def material_move(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "materials")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        mid = str(body.get("material_id") or "")
        if not self._prod_find(org, "material", mid):
            return {"ok": False, "error": "not_found", "message_ru": "Материал не найден"}
        qty = _num(body.get("quantity"))
        if qty is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите количество"}
        return await self._add_material_move(
            org,
            movement_type=str(body.get("movement_type") or "RECEIPT"),
            quantity=qty,
            material_id=mid,
            role=role,
            extra=body,
        )

    async def issue_to_field(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "materials")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        qty = _num(body.get("quantity"))
        if not qty:
            return {"ok": False, "error": "validation", "message_ru": "Укажите количество"}
        mov = await self._add_material_move(
            org,
            movement_type="ISSUE",
            quantity=qty,
            material_id=str(body.get("material_id") or ""),
            role=role,
            extra={**body, "title": body.get("title") or "Выдача в поле"},
        )
        if not mov.get("ok"):
            return mov
        unit_cost = _num(body.get("unit_cost") or body.get("cost_basis"))
        if unit_cost is not None and can(role, "finance"):
            mat = self._prod_find(org, "material", str(body.get("material_id") or ""))
            cat = str((mat or {}).get("category") or "other")
            await self.add_field_cost(
                organization_id,
                {
                    "field_id": body.get("field_id"),
                    "season_id": body.get("season_id"),
                    "category": cat if cat in {c for c, _ in COST_CATEGORIES} else "other",
                    "amount": round(qty * unit_cost, 2),
                    "source": "material_movement",
                    "source_id": (mov.get("item") or {}).get("id"),
                    "currency": body.get("currency") or "UAH",
                },
                role,
            )
        return mov

    async def add_field_cost(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "finance") or self._prod_write(role, "costs")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        amt = _num(body.get("amount"))
        if amt is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму"}
        if not body.get("source") and not body.get("source_id"):
            return {"ok": False, "error": "validation", "message_ru": "У расхода должна быть исходная запись"}
        cat = str(body.get("category") or "other")
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "field_cost",
            {
                "title": body.get("title") or dict(COST_CATEGORIES).get(cat, "Расход"),
                "category": cat,
                "amount": amt,
                "currency": body.get("currency") or "UAH",
                "field_id": body.get("field_id"),
                "season_id": body.get("season_id"),
                "source": body.get("source"),
                "source_id": body.get("source_id"),
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def create_maintenance(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "maintenance")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "maintenance",
            {
                "title": body.get("title") or body.get("maintenance_type") or "ТО",
                "machine_id": body.get("machine_id"),
                "maintenance_type": body.get("maintenance_type") or "service",
                "due_hours": _num(body.get("due_engine_hours") or body.get("due_hours")),
                "due_at": body.get("due_date") or body.get("due_at"),
                "actual_at": body.get("actual_date") or body.get("actual_at"),
                "cost": _num(body.get("cost")),
                "provider": body.get("service_provider") or body.get("provider"),
                "status": body.get("status") or "planned",
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def create_harvest_plan(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "harvest")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        yha = _num(body.get("planned_yield_t_ha") or body.get("planned_yield"))
        area = _num(body.get("area_ha")) or _num(field.get("area_ha"))
        total = _num(body.get("planned_total_tonnes"))
        if total is None and yha is not None and area:
            total = round(yha * area, 4)
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "harvest_plan",
            {
                "title": body.get("title") or f"План уборки {field.get('name')}",
                "field_id": field["id"],
                "season_id": body.get("season_id") or (self._current_season(org, str(field["id"])) or {}).get("id"),
                "crop": body.get("crop") or (self._current_season(org, str(field["id"])) or {}).get("crop"),
                "planned_at": body.get("planned_date") or body.get("planned_at"),
                "planned_yield_t_ha": yha,
                "planned_total_tonnes": total,
                "combine_id": body.get("combine") or body.get("combine_id") or body.get("machine_id"),
                "warehouse_id": body.get("warehouse_id"),
                "workspace_id": self._ws(body),
            },
            role,
        )

    async def record_harvest(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or self._prod_write(role, "harvest")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        field = self._prod_find(org, "agro_field", str(body.get("field_id") or ""))
        if not field:
            return {"ok": False, "error": "not_found", "message_ru": "Поле не найдено"}
        tonnes = _num(body.get("actual_tonnes") or body.get("tonnes"))
        area = _num(body.get("area_harvested") or body.get("area_ha")) or _num(field.get("area_ha"))
        if tonnes is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите фактические тонны. Не выдумываем урожай."}
        yld = _round4(tonnes / area) if area else None
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "harvest_actual",
            {
                "title": body.get("title") or f"Урожай {field.get('name')}",
                "field_id": field["id"],
                "season_id": body.get("season_id") or (self._current_season(org, str(field["id"])) or {}).get("id"),
                "harvested_at": body.get("date") or _now().date().isoformat(),
                "combine_id": body.get("combine") or body.get("machine_id"),
                "area_harvested": area,
                "actual_tonnes": tonnes,
                "moisture": _num(body.get("moisture")),
                "quality": body.get("quality"),
                "yield_t_ha": yld,
                "workspace_id": self._ws(body),
            },
            role,
        )
        if saved.get("ok") and saved["item"].get("season_id"):
            await self.update_entity(org, "crop_season", str(saved["item"]["season_id"]), {"status": "harvest"}, role)  # type: ignore[attr-defined]
        return {**saved, "yield_t_ha": yld}

    async def harvest_to_warehouse(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        """Field harvest → 2.2 truck / weighing / warehouse receipt / lot. No second inventory."""
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        hid = str(body.get("harvest_id") or "")
        harvest = self._prod_find(org, "harvest_actual", hid)
        if not harvest:
            return {"ok": False, "error": "not_found", "message_ru": "Запись урожая не найдена"}
        tonnes = _num(harvest.get("actual_tonnes"))
        if not tonnes:
            return {"ok": False, "error": "validation", "message_ru": "Нет фактических тонн"}
        field = self._prod_find(org, "agro_field", str(harvest.get("field_id") or ""))
        season = self._prod_find(org, "crop_season", str(harvest.get("season_id") or ""))
        crop = (season or {}).get("crop") or "Пшеница"
        op_id = body.get("operation_id")
        if not op_id:
            created = await self.create_operation(  # type: ignore[attr-defined]
                org,
                {
                    "crop": crop,
                    "planned_qty": tonnes,
                    "warehouse_id": body.get("warehouse_id"),
                    "title": f"Урожай { (field or {}).get('name') }",
                    "origin": "field_harvest",
                },
                role,
            )
            if not created.get("ok"):
                return created
            op_id = created["item"]["id"]
        if body.get("plate") or body.get("truck"):
            await self.add_truck_run(  # type: ignore[attr-defined]
                org,
                {"operation_id": op_id, "plate": body.get("plate") or body.get("truck"), "planned_weight": tonnes, "idempotency_key": f"harvest-truck-{hid}"},
                role,
            )
        await self.add_weighing(  # type: ignore[attr-defined]
            org,
            {"operation_id": op_id, "gross": tonnes + 1, "tare": 1, "scale": "receiving", "unit": "т", "idempotency_key": f"harvest-w-{hid}"},
            role,
        )
        rec = await self.receive_operation(  # type: ignore[attr-defined]
            org,
            {"operation_id": op_id, "warehouse_id": body.get("warehouse_id"), "idempotency_key": f"harvest-receipt-{hid}"},
            role,
        )
        if rec.get("ok") and rec.get("item"):
            await self.update_entity(  # type: ignore[attr-defined]
                org,
                "inventory_lot",
                str(rec["item"]["id"]),
                {"field_id": harvest.get("field_id"), "harvest_id": hid, "season_id": harvest.get("season_id")},
                role,
            )
            await self.update_entity(org, "harvest_actual", hid, {"operation_id": op_id, "lot_id": rec["item"]["id"]}, role)  # type: ignore[attr-defined]
        return {"ok": bool(rec.get("ok")), "operation_id": op_id, "receipt": rec, "harvest_id": hid}

    def _prod_trace(self, org: str, field_id: str, direction: str) -> list[dict[str, str]]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        steps: list[dict[str, str]] = [{"kind": "agro_field", "id": field_id, "label": "field"}]
        season = self._current_season(org, field_id)
        if season:
            steps.append({"kind": "crop_season", "id": str(season.get("id")), "label": str(season.get("crop") or "season")})
        works = [w for w in active_only(bag.get("field_work") or []) if str(w.get("field_id")) == field_id]
        if direction == "back":
            sow = next((w for w in works if str(w.get("work_type")) == "sowing"), None)
            if sow:
                steps.append({"kind": "field_work", "id": str(sow.get("id")), "label": "sowing"})
            for m in active_only(bag.get("material_movement") or []):
                if str(m.get("field_id")) == field_id and str(m.get("movement_type")) == "ISSUE":
                    steps.append({"kind": "material_movement", "id": str(m.get("id")), "label": "input"})
                    break
        else:
            for h in active_only(bag.get("harvest_actual") or []):
                if str(h.get("field_id")) == field_id:
                    steps.append({"kind": "harvest_actual", "id": str(h.get("id")), "label": "harvest"})
                    if h.get("lot_id"):
                        steps.append({"kind": "inventory_lot", "id": str(h.get("lot_id")), "label": "lot"})
                    if h.get("operation_id"):
                        steps.append({"kind": "agro_operation", "id": str(h.get("operation_id")), "label": "sale-op"})
        return [s for s in steps if s.get("id")]

    async def crop_costs(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        if not (can(role, "finance") or can(role, "margins")):
            return {"ok": True, "items": [], "masked": True, "message_ru": "Нет доступа к себестоимости"}
        q = query or {}
        year = q.get("season") or q.get("year")
        region = (q.get("region") or "").lower()
        by: dict[str, dict[str, Any]] = {}
        for field in self._prod_scope(org, "agro_field", q.get("workspace_id")):
            if region and region not in _s(field.get("region")).lower():
                continue
            season = self._current_season(org, str(field["id"]))
            if year and str((season or {}).get("year")) != str(year):
                continue
            crop = str((season or {}).get("crop") or "Прочее")
            m = self._field_metrics(org, field, season, role)
            b = by.setdefault(crop, {"crop": crop, "area": 0.0, "total_cost": 0.0, "yield_t": 0.0, "n": 0, "cost_known": False, "yield_known": False})
            b["area"] += m.get("area_ha") or 0
            if m.get("total_cost") is not None:
                b["total_cost"] += m["total_cost"]
                b["cost_known"] = True
            if m.get("harvest_tonnes"):
                b["yield_t"] += m["harvest_tonnes"]
                b["yield_known"] = True
            b["n"] += 1
        items = []
        for b in by.values():
            items.append({
                "crop": b["crop"],
                "area": round(b["area"], 2),
                "total_cost": round(b["total_cost"], 2) if b["cost_known"] else None,
                "total_yield": round(b["yield_t"], 4) if b["yield_known"] else None,
                "cost_ha": round(b["total_cost"] / b["area"], 2) if b["cost_known"] and b["area"] else None,
                "cost_t": round(b["total_cost"] / b["yield_t"], 2) if b["cost_known"] and b["yield_known"] and b["yield_t"] else None,
            })
        return {"ok": True, "items": items}

    async def crop_structure(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        by: dict[str, float] = {}
        total = 0.0
        for field in self._prod_scope(org, "agro_field"):
            season = self._current_season(org, str(field["id"]))
            crop = str((season or {}).get("crop") or "")
            area = _num(field.get("area_ha")) or 0
            if not crop or not area:
                continue
            by[crop] = by.get(crop, 0) + area
            total += area
        if not total:
            return {"ok": True, "items": [], "message_ru": "Нет данных"}
        items = [{"crop": k, "area": round(v, 2), "pct": round(v / total * 100, 1), "color": self._crop_color(k)} for k, v in sorted(by.items(), key=lambda x: -x[1])]
        return {"ok": True, "items": items, "total_ha": round(total, 2)}

    async def agronomist_today(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        today = _now().date().isoformat()
        works = self._prod_scope(org, "field_work")
        mats = self._prod_scope(org, "material")
        issues = self._prod_scope(org, "field_issue")
        maint = self._prod_scope(org, "maintenance")

        def wt(code: str) -> int:
            return len([w for w in works if str(w.get("work_type")) == code and str(w.get("planned_at") or "")[:10] == today])

        shortage = 0
        for m in mats:
            if self._material_balance(org, str(m["id"])) <= 1e-6:
                shortage += 1
        wx_risk = 0
        for f in self._prod_scope(org, "agro_field"):
            w = self._field_weather(org, f)
            if w and str(w.get("level")) in {"High", "Medium"}:
                wx_risk += 1
        overdue = len([w for w in works if str(w.get("status")) == "overdue" or (str(w.get("planned_at") or "")[:10] < today and str(w.get("status")) == "planned")])
        machine_issues = len([i for i in issues if str(i.get("issue_type")) == "machinery" and str(i.get("status")) not in {"done", "closed"}])
        metrics = [
            {"id": "sowing", "label_ru": "Посев", "value": wt("sowing"), "view": "fields", "filter": "sowing"},
            {"id": "spraying", "label_ru": "Опрыскивание", "value": wt("spraying"), "view": "fields", "filter": "spraying"},
            {"id": "fertilizer", "label_ru": "Удобрение", "value": wt("fertilizer"), "view": "fields", "filter": "fertilizer"},
            {"id": "harvest", "label_ru": "Уборка", "value": wt("harvest"), "view": "fields", "filter": "harvest"},
            {"id": "overdue", "label_ru": "Просроченные работы", "value": overdue, "view": "fields", "filter": "overdue"},
            {"id": "weather", "label_ru": "Погодные риски", "value": wx_risk, "view": "weather"},
            {"id": "machines", "label_ru": "Проблемы техники", "value": machine_issues + len([m for m in maint if str(m.get("status")) == "overdue"]), "view": "machinery"},
            {"id": "shortage", "label_ru": "Нехватка материалов", "value": shortage, "view": "fields", "filter": "materials"},
        ]
        return {"ok": True, "metrics": metrics, "version": PROD_VERSION}

    async def director_production(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        fields = self._prod_scope(org, "agro_field")
        land = round(sum(_num(f.get("area_ha")) or 0 for f in fields), 2)
        sown = 0.0
        for f in fields:
            s = self._current_season(org, str(f["id"]))
            if s and str(s.get("status")) in {"sown", "vegetation", "harvest", "closed"}:
                sown += _num(s.get("actual_area")) or _num(f.get("area_ha")) or 0
        works = self._prod_scope(org, "field_work")
        done = len([w for w in works if str(w.get("status")) == "done"])
        pct = round(done / len(works) * 100, 1) if works else None
        fuel = 0.0
        fuel_known = False
        for m in self._prod_scope(org, "material_movement"):
            if str(m.get("movement_type")) != "ISSUE":
                continue
            mat = self._prod_find(org, "material", str(m.get("material_id") or ""))
            if str((mat or {}).get("category")) == "fuel":
                fuel += _qty(m.get("quantity"))
                fuel_known = True
        harvest_t = sum(_num(h.get("actual_tonnes")) or 0 for h in self._prod_scope(org, "harvest_actual"))
        harvested_ha = sum(_num(h.get("area_harvested")) or 0 for h in self._prod_scope(org, "harvest_actual"))
        yld = _round4(harvest_t / harvested_ha) if harvested_ha and harvest_t else None
        show = can(role, "finance") or can(role, "margins")
        total_cost = None
        if show:
            acc = 0.0
            any_c = False
            for c in self._prod_scope(org, "field_cost"):
                amt = _num(c.get("amount"))
                if amt is None:
                    continue
                any_c = True
                acc += amt
            total_cost = round(acc, 2) if any_c else None
        structure = await self.crop_structure(organization_id, role)
        return {
            "ok": True,
            "land_bank_ha": land or None,
            "sown_ha": sown or None,
            "work_completion_pct": pct,
            "fuel": round(fuel, 3) if fuel_known else None,
            "harvest_tonnes": harvest_t or None,
            "yield_t_ha": yld,
            "cost_ha": round(total_cost / land, 2) if show and total_cost is not None and land else None,
            "cost_t": round(total_cost / harvest_t, 2) if show and total_cost is not None and harvest_t else None,
            "crop_structure": structure.get("items") or [],
            "message_ru": None if land else "Нет данных",
        }

    async def create_field_issue(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        itype = str(body.get("issue_type") or body.get("type") or "other")
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "field_issue",
            {
                "title": body.get("title") or dict(ISSUE_TYPES).get(itype, "Проблема"),
                "issue_type": itype,
                "field_id": body.get("field_id"),
                "severity": body.get("severity") or "MEDIUM",
                "location": body.get("location"),
                "description": body.get("description") or body.get("title"),
                "responsible": body.get("responsible"),
                "deadline": body.get("deadline"),
                "status": body.get("status") or "OPEN",
                "workspace_id": self._ws(body),
            },
            role,
        )
        if saved.get("ok") and body.get("create_task"):
            await self.create_task_from_entity(  # type: ignore[attr-defined]
                org,
                {
                    "title": saved["item"]["title"],
                    "entity_type": "field_issue",
                    "entity_id": saved["item"]["id"],
                    "field_id": body.get("field_id"),
                    "due_at": body.get("deadline"),
                    "owner": body.get("responsible"),
                },
                role,
            )
        return saved

    async def evaluate_production_alerts(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        today = _now().date()
        created = 0
        for w in self._prod_scope(org, "field_work"):
            due = str(w.get("planned_at") or "")[:10]
            if due and due < today.isoformat() and str(w.get("status")) in {"planned", "in_progress"}:
                await self._emit_notification(  # type: ignore[attr-defined]
                    org, title=f"Просрочена работа: {w.get('title')}", entity_type="field_work", entity_id=str(w.get("id")),
                    deeplink=f"/workspace/agro?view=fields&id={w.get('field_id')}", extra={"kind": "work_overdue"},
                )
                created += 1
                await self.update_entity(org, "field_work", str(w["id"]), {"status": "overdue"}, role)  # type: ignore[attr-defined]
        soon = (today + timedelta(days=7)).isoformat()
        for m in self._prod_scope(org, "maintenance"):
            due = str(m.get("due_at") or "")[:10]
            if not due or str(m.get("status")) in {"done", "closed"}:
                continue
            title = "ТО просрочено" if due < today.isoformat() else ("ТО скоро" if due <= soon else None)
            if title:
                await self._emit_notification(  # type: ignore[attr-defined]
                    org, title=f"{title}: {m.get('title')}", entity_type="maintenance", entity_id=str(m.get("id")),
                    deeplink="/workspace/agro?view=machinery", extra={"kind": "maintenance_due"},
                )
                created += 1
        for f in self._prod_scope(org, "agro_field"):
            lease = str(f.get("lease_until") or "")[:10]
            if lease and lease <= soon:
                await self._emit_notification(  # type: ignore[attr-defined]
                    org, title=f"Истекает аренда: {f.get('name')}", entity_type="agro_field", entity_id=str(f.get("id")),
                    deeplink=f"/workspace/agro?view=fields&id={f.get('id')}", extra={"kind": "lease_expiry"},
                )
                created += 1
        return {"ok": True, "created": created}

    async def bootstrap_production_demo(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        existing = next((s for s in active_only(self._bag(org).get("settings") or []) if s.get("production_demo_loaded")), None)  # type: ignore[attr-defined]
        if existing:
            return {"ok": True, "already": True, "message_ru": "Демо AGRO Production уже загружено"}
        field = await self.create_field(org, {"name": "[DEMO] Поле 17", "number": "17", "area_ha": 124, "region": "Одесская", "is_demo": True}, role)
        if not field.get("ok"):
            return field
        await self.create_season(org, {"field_id": field["item"]["id"], "crop": "Пшеница", "year": 2026}, role)
        await self.create_entity(org, "settings", {"name": "production_demo", "production_demo_loaded": True, "title": "[DEMO] AGRO Production", "is_demo": True}, role)  # type: ignore[attr-defined]
        return {"ok": True, "item": field["item"], "message_ru": "DEMO AGRO Production загружено. Строки помечены [DEMO]."}

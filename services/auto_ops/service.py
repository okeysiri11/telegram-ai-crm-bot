"""AUTO 1.0 ops service — private import/dealership desk.

Org-scoped. Postgres persist with in-memory fallback (Legal/Agro pattern).
Never seeds fake financial or logistics records.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.auto_ops_repository import AutoOpsRepository, row_to_dict
from services.auto_ops.catalog import (
    DOCUMENT_IDS,
    DOCUMENT_OWNERS,
    EXPENSE_IDS,
    EXPENSE_LABELS,
    FINANCE_KPI_GROUPS,
    KPI_STATUS_GROUPS,
    PHOTO_IDS,
    STATUS_IDS,
    STATUS_LABELS,
    catalogs,
    lifecycle_for_status,
)
from services.auto_ops.files import read_bytes, validate_upload, write_bytes
from services.auto_ops.analytics import ANALYTICS_BAG_KEYS, AutoOpsAnalyticsMixin
from services.auto_ops.analytics_catalog import ACCOUNT_TYPES, ECONOMICS_FILTERS, PERIODS
from services.auto_ops.crm import CRM_BAG_KEYS, AutoOpsCrmMixin
from services.auto_ops.documents import DOCUMENTS_BAG_KEYS, AutoOpsDocumentsMixin
from services.auto_ops.documents_catalog import SALE_PACKAGE_ITEMS, REGISTRATION_PACKAGE_ITEMS, documents_catalogs, extract_vin_hint
from services.auto_ops.customs import CUSTOMS_BAG_KEYS, AutoOpsCustomsMixin
from services.auto_ops.customs_catalog import CUSTOMS_EXPENSE_IDS
from services.auto_ops.customs_ops import AutoOpsCustomsOpsMixin
from services.auto_ops.logistics import LOGISTICS_BAG_KEYS, AutoOpsLogisticsMixin
from services.auto_ops.logistics_ops import AutoOpsLogisticsOpsMixin
from services.auto_ops.logistics_catalog import LOGISTICS_EXPENSE_IDS
from services.auto_ops.rbac import can, normalize_role, require, roles_catalog
from services.auto_ops.telegram import TELEGRAM_BAG_KEYS, AutoOpsTelegramMixin, reset_telegram_runtime_for_tests
from services.auto_ops.telegram_boundary import telegram_boundary
from services.auto_ops.vin import normalize_vin, validate_vin

logger = logging.getLogger(__name__)

BAG_KEYS = ("vehicles", "expenses", "documents", "photos", "clients", "tasks", "audit", "files") + LOGISTICS_BAG_KEYS + CUSTOMS_BAG_KEYS + CRM_BAG_KEYS + TELEGRAM_BAG_KEYS + ANALYTICS_BAG_KEYS + DOCUMENTS_BAG_KEYS

VEHICLE_FIELDS = (
    "vin",
    "internal_number",
    "status",
    "manufacturer",
    "model",
    "year",
    "trim",
    "body_type",
    "fuel_type",
    "engine",
    "transmission",
    "drive_type",
    "exterior_color",
    "interior_color",
    "mileage",
    "mileage_unit",
    "country_of_origin",
    "purchase_country",
    "auction_name",
    "auction_lot",
    "auction_url",
    "purchase_date",
    "purchase_price",
    "purchase_currency",
    "buyer_fee",
    "estimated_market_value",
    "location_current",
    "origin_port",
    "destination_port",
    "assigned_manager_id",
    "client_id",
    "cover_photo_id",
    "sale_price_expected",
    "sale_price_actual",
    "sale_date",
    "sale_currency",
    "notes",
    "is_demo",
    "workspace_id",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _org(organization_id: str | None, tenant_id: str | None = None) -> str:
    return (organization_id or tenant_id or "default").strip() or "default"


def _num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _opt_num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _year(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        y = int(value)
    except (TypeError, ValueError):
        return None
    if 1950 <= y <= 2100:
        return y
    return None


class AutoOpsService(AutoOpsLogisticsMixin, AutoOpsLogisticsOpsMixin, AutoOpsCustomsMixin, AutoOpsCustomsOpsMixin, AutoOpsCrmMixin, AutoOpsTelegramMixin, AutoOpsAnalyticsMixin, AutoOpsDocumentsMixin):
    def __init__(self) -> None:
        self._mem: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._hydrated: set[str] = set()
        self._tg_upload_pending: dict[int, dict[str, Any]] = {}

    def _now(self) -> str:
        return _now()

    def _org(self, organization_id: str | None, tenant_id: str | None = None) -> str:
        return _org(organization_id, tenant_id)

    def _bag(self, org: str) -> dict[str, list[dict[str, Any]]]:
        if org not in self._mem:
            self._mem[org] = {k: [] for k in BAG_KEYS}
        for key in BAG_KEYS:
            self._mem[org].setdefault(key, [])
        return self._mem[org]

    async def ensure_hydrated(self, organization_id: str) -> None:
        org = _org(organization_id)
        if org in self._hydrated:
            return
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AutoOpsRepository(session)
                bag = self._bag(org)
                for kind, key in (
                    ("vehicle", "vehicles"),
                    ("expense", "expenses"),
                    ("document", "documents"),
                    ("photo", "photos"),
                    ("client", "clients"),
                    ("task", "tasks"),
                    ("audit", "audit"),
                    ("file", "files"),
                    ("shipment", "shipments"),
                    ("carrier", "carriers"),
                    ("driver", "drivers"),
                    ("truck", "trucks"),
                    ("container", "containers"),
                    ("container_vehicle", "container_vehicles"),
                    ("vessel", "vessels"),
                    ("port", "ports"),
                    ("logistics_event", "logistics_events"),
                    ("notification", "notifications"),
                    ("logistics_setting", "logistics_settings"),
                    ("logistics_provider", "logistics_providers"),
                    ("customs_case", "customs_cases"),
                    ("broker", "brokers"),
                    ("customs_setting", "customs_settings"),
                    ("deal", "deals"),
                    ("reservation", "reservations"),
                    ("sale", "sales"),
                    ("receipt", "receipts"),
                    ("telegram_member", "telegram_members"),
                    ("telegram_outbox", "telegram_outbox"),
                    ("status_history", "status_history"),
                    ("finance_account", "finance_accounts"),
                    ("document_template", "document_templates"),
                ):
                    try:
                        bag[key] = [row_to_dict(r) for r in await repo.list_kind(kind, org)]
                    except Exception as kind_exc:
                        logger.warning("auto_ops hydrate %s skipped: %s", kind, kind_exc)
                        bag.setdefault(key, [])
                        try:
                            await session.rollback()
                        except Exception:
                            pass
        except Exception as exc:
            logger.warning("auto_ops hydrate skipped: %s", exc)
        self._hydrated.add(org)

    async def _persist(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AutoOpsRepository(session)
                row = await repo.insert(kind, data)
                return row_to_dict(row)
        except Exception as exc:
            logger.warning("auto_ops persist %s failed (memory kept): %s", kind, exc)
            return data

    async def _persist_update(self, kind: str, item_id: str, patch: dict[str, Any]) -> None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AutoOpsRepository(session)
                await repo.update(kind, item_id, patch)
        except Exception as exc:
            logger.warning("auto_ops update %s failed (memory kept): %s", kind, exc)

    async def _persist_delete(self, kind: str, item_id: str) -> None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AutoOpsRepository(session)
                await repo.delete(kind, item_id)
        except Exception as exc:
            logger.warning("auto_ops delete %s failed (memory kept): %s", kind, exc)

    async def _audit(
        self,
        *,
        organization_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        role: str | None,
        actor_id: str | None = None,
        old_value: Any = None,
        new_value: Any = None,
        summary: str | None = None,
    ) -> dict[str, Any]:
        org = _org(organization_id)
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "actor_id": actor_id or normalize_role(role),
            "actor_role": normalize_role(role),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "summary": summary or action,
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("audit", item)
        self._bag(org)["audit"].insert(0, saved)
        return saved

    def roles(self) -> list[dict[str, Any]]:
        return roles_catalog()

    def catalogs(self) -> dict[str, Any]:
        data = catalogs()
        data["economics_filters"] = ECONOMICS_FILTERS
        data["finance_periods"] = PERIODS
        data["finance_account_types"] = ACCOUNT_TYPES
        data.update(documents_catalogs())
        return data

    def telegram(self) -> dict[str, Any]:
        return telegram_boundary()

    def _find(self, org: str, key: str, item_id: str) -> dict[str, Any] | None:
        for item in self._bag(org)[key]:
            if str(item.get("id")) == str(item_id):
                return item
        return None

    def _client_name(self, org: str, client_id: str | None) -> str:
        if not client_id:
            return ""
        c = self._find(org, "clients", client_id)
        return str(c.get("name") or "") if c else ""

    def _cover_file(self, org: str, vehicle: dict[str, Any]) -> str | None:
        cover = vehicle.get("cover_photo_id")
        if cover:
            return str(cover)
        photos = [p for p in self._bag(org)["photos"] if p.get("vehicle_id") == vehicle.get("id")]
        if photos:
            return str(photos[0].get("file_id") or photos[0].get("id"))
        return None

    def _expense_base(self, exp: dict[str, Any]) -> float:
        if exp.get("amount_base_currency") not in (None, ""):
            return _num(exp.get("amount_base_currency"))
        amount = _num(exp.get("amount"))
        rate = _num(exp.get("exchange_rate")) or 1.0
        return round(amount * rate, 2)

    def _vehicle_invested(self, org: str, vehicle_id: str) -> float:
        total = 0.0
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("vehicle_id")) == str(vehicle_id) and str(exp.get("payment_status")) != "cancelled":
                total += self._expense_base(exp)
        return round(total, 2)

    def _finance_snapshot(self, org: str, vehicle: dict[str, Any]) -> dict[str, Any]:
        vid = str(vehicle.get("id"))
        lines: list[dict[str, Any]] = []
        totals: dict[str, float] = {k: 0.0 for k in FINANCE_KPI_GROUPS}
        invested = 0.0
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("vehicle_id")) != vid:
                continue
            if str(exp.get("payment_status")) == "cancelled":
                continue
            base = self._expense_base(exp)
            invested += base
            cat = str(exp.get("category") or "OTHER")
            for group, ids in FINANCE_KPI_GROUPS.items():
                if cat in ids:
                    totals[group] += base
            lines.append(
                {
                    "id": exp.get("id"),
                    "category": cat,
                    "label_ru": EXPENSE_LABELS.get(cat, cat),
                    "amount": _num(exp.get("amount")),
                    "currency": exp.get("currency") or "USD",
                    "amount_base_currency": base,
                    "description": exp.get("description"),
                    "payment_status": exp.get("payment_status"),
                    **self.finance_document_flag(org, exp),
                }
            )
        invested = round(invested, 2)
        landed = self._landed_cost(org, vid)
        expected = _opt_num(vehicle.get("sale_price_expected"))
        actual = _opt_num(vehicle.get("sale_price_actual"))
        sold = str(vehicle.get("status") or "") == "SOLD"
        return {
            "lines": lines,
            "cost": invested,
            "groups": {k: round(v, 2) for k, v in totals.items()},
            "sale_price_expected": expected,
            "sale_price_actual": actual,
            "profit_expected": round(expected - invested, 2) if expected is not None else None,
            "profit_actual": round(actual - invested, 2) if actual is not None else None,
            "actual_profit": round(actual - landed["landed_cost"] - landed["selling_costs"], 2) if sold and actual is not None else None,
            "source": "expense_records",
            "landed": landed,
            "note_ru": "Суммы считаются только по фактическим расходам. Пустые категории не заполняются. Фактическая прибыль — только для проданных авто.",
        }

    def _attention(self, org: str, vehicles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for v in vehicles:
            status = str(v.get("status") or "")
            if status == "CANCELLED":
                continue
            reasons: list[str] = []
            if not v.get("location_current"):
                reasons.append("Нет текущего местоположения")
            if status in {"SEA_TRANSIT", "DESTINATION_PORT", "CUSTOMS"} and not v.get("destination_port"):
                reasons.append("Не указан порт назначения")
            if status in KPI_STATUS_GROUPS["purchased"] and self._vehicle_invested(org, str(v.get("id"))) == 0:
                reasons.append("Нет расходов — себестоимость неизвестна")
            if status in {"READY_FOR_SALE", "RESERVED"} and not v.get("sale_price_expected"):
                reasons.append("Нет ожидаемой цены продажи")
            if status == "RESERVED" and not v.get("client_id"):
                reasons.append("Резерв без клиента")
            if reasons:
                out.append(
                    {
                        "vehicle_id": v.get("id"),
                        "title": self._vehicle_title(v),
                        "status": status,
                        "status_ru": STATUS_LABELS.get(status, status),
                        "reasons": reasons,
                    }
                )
        return out[:20]

    def _vehicle_title(self, v: dict[str, Any]) -> str:
        parts = [str(v.get("year") or "").strip(), str(v.get("manufacturer") or "").strip(), str(v.get("model") or "").strip()]
        title = " ".join(p for p in parts if p)
        return title or str(v.get("vin") or "Автомобиль")

    def _public_vehicle(self, org: str, v: dict[str, Any]) -> dict[str, Any]:
        status = str(v.get("status") or "")
        invested = self._vehicle_invested(org, str(v.get("id")))
        counters = self.document_counters_for_vehicle(org, v)
        return {
            **v,
            "title": self._vehicle_title(v),
            "status_ru": STATUS_LABELS.get(status, status),
            "client_name": self._client_name(org, v.get("client_id")),
            "invested": invested,
            "cover_file_id": self._cover_file(org, v),
            "lifecycle": lifecycle_for_status(status),
            "document_count": counters.get("document_count"),
            "documents_missing": counters.get("missing_count"),
        }

    async def dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        vehicles = [v for v in self._bag(org)["vehicles"] if str(v.get("status")) != "CANCELLED"]
        all_v = self._bag(org)["vehicles"]

        def count(group: str) -> int:
            ids = KPI_STATUS_GROUPS[group]
            return sum(1 for v in all_v if str(v.get("status")) in ids)

        expenses = [e for e in self._bag(org)["expenses"] if str(e.get("payment_status")) != "cancelled"]
        purchase_cost = 0.0
        logistics = 0.0
        customs = 0.0
        other = 0.0
        invested = 0.0
        for exp in expenses:
            base = self._expense_base(exp)
            invested += base
            cat = str(exp.get("category") or "OTHER")
            if cat in FINANCE_KPI_GROUPS["purchase_cost"]:
                purchase_cost += base
            elif cat in FINANCE_KPI_GROUPS["logistics"]:
                logistics += base
            elif cat in FINANCE_KPI_GROUPS["customs"]:
                customs += base
            else:
                other += base

        expected_revenue = 0.0
        actual_revenue = 0.0
        expected_profit = 0.0
        actual_profit = 0.0
        for v in all_v:
            vid = str(v.get("id"))
            cost = self._vehicle_invested(org, vid)
            st = str(v.get("status") or "")
            exp_price = _opt_num(v.get("sale_price_expected"))
            act_price = _opt_num(v.get("sale_price_actual"))
            if st == "SOLD" and act_price is not None:
                actual_revenue += act_price
                actual_profit += act_price - cost
            elif st != "CANCELLED" and exp_price is not None:
                expected_revenue += exp_price
                expected_profit += exp_price - cost

        finance_ok = can(role, "finance")
        cards = {
            "vehicles_total": len(all_v),
            "purchased": count("purchased"),
            "in_transit": count("in_transit"),
            "at_port": count("at_port"),
            "at_customs": count("at_customs"),
            "in_ukraine": count("in_ukraine"),
            "in_preparation": count("in_preparation"),
            "for_sale": count("for_sale"),
            "sold": count("sold"),
        }
        finance = {
            "purchase_cost": round(purchase_cost, 2),
            "logistics": round(logistics, 2),
            "customs": round(customs, 2),
            "other": round(other, 2),
            "invested": round(invested, 2),
            "expected_revenue": round(expected_revenue, 2),
            "actual_revenue": round(actual_revenue, 2),
            "expected_profit": round(expected_profit, 2),
            "actual_profit": round(actual_profit, 2),
            "currency": "USD",
            "from_records": True,
        }
        if not finance_ok:
            finance = {"restricted": True, "message_ru": "Финансовые KPI доступны директору и бухгалтеру."}
        return {
            "ok": True,
            "sprint": "AUTO_1.8.5",
            "private": True,
            "cards": cards,
            "finance": finance,
            "attention": self._attention(org, vehicles),
            "counts": {
                "clients": len(self._bag(org)["clients"]),
                "tasks_open": sum(1 for t in self._bag(org)["tasks"] if t.get("status") in {"open", "in_progress"}),
                "documents": len(self._bag(org)["documents"]),
            },
            "role": normalize_role(role),
        }

    async def list_vehicles(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        q = query or {}
        items = [self._public_vehicle(org, v) for v in self._bag(org)["vehicles"]]
        search = (q.get("q") or q.get("search") or "").strip().upper()
        status = (q.get("status") or "").strip().upper()
        country = (q.get("country") or q.get("purchase_country") or "").strip().lower()
        manager = (q.get("manager") or q.get("assigned_manager_id") or "").strip()
        auction = (q.get("auction") or q.get("auction_name") or "").strip().lower()
        location = (q.get("location") or q.get("location_current") or "").strip().lower()
        date_from = (q.get("purchase_date_from") or "").strip()
        date_to = (q.get("purchase_date_to") or "").strip()
        if status:
            items = [v for v in items if str(v.get("status")) == status]
        if country:
            items = [v for v in items if country in str(v.get("purchase_country") or "").lower() or country in str(v.get("country_of_origin") or "").lower()]
        if manager:
            items = [v for v in items if str(v.get("assigned_manager_id") or "") == manager]
        if auction:
            items = [v for v in items if auction in str(v.get("auction_name") or "").lower()]
        if location:
            items = [v for v in items if location in str(v.get("location_current") or "").lower()]
        if date_from:
            items = [v for v in items if str(v.get("purchase_date") or "") >= date_from]
        if date_to:
            items = [v for v in items if str(v.get("purchase_date") or "") <= date_to]
        if search:
            def hay(v: dict[str, Any]) -> str:
                return " ".join(
                    str(v.get(k) or "")
                    for k in ("vin", "manufacturer", "model", "auction_lot", "internal_number", "client_name", "title")
                ).upper()

            items = [v for v in items if search in hay(v)]
        sort = (q.get("sort") or "updated_at").strip()
        reverse = (q.get("dir") or "desc").lower() != "asc"
        items.sort(key=lambda v: str(v.get(sort) or ""), reverse=reverse)
        return {"ok": True, "items": items, "total": len(items)}

    async def get_vehicle(self, organization_id: str, vehicle_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        v = self._find(org, "vehicles", vehicle_id)
        if not v:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль не найден"}
        bag = self._bag(org)
        photos = [p for p in bag["photos"] if str(p.get("vehicle_id")) == str(vehicle_id)]
        docs = [d for d in bag["documents"] if str(d.get("vehicle_id")) == str(vehicle_id)]
        tasks = [t for t in bag["tasks"] if str(t.get("vehicle_id")) == str(vehicle_id)]
        audit = [a for a in bag["audit"] if str(a.get("entity_id")) == str(vehicle_id)]
        raw_client = self._find(org, "clients", str(v.get("client_id") or "")) if v.get("client_id") else None
        client = self._redact_client(raw_client, role) if raw_client else None
        item = self._public_vehicle(org, v)
        finance = self._finance_snapshot(org, v)
        if not can(role, "finance"):
            finance = {"restricted": True, "message_ru": "Финансы доступны директору и бухгалтеру."}
        logistics = self.vehicle_logistics_block(org, str(vehicle_id), role)
        customs = self.vehicle_customs_block(org, str(vehicle_id), role)
        crm = self.vehicle_crm_block(org, str(vehicle_id), role)
        sale_pack = self._eval_package(org, v, SALE_PACKAGE_ITEMS)
        registration_pack = self._eval_package(org, v, REGISTRATION_PACKAGE_ITEMS)
        return {
            "ok": True,
            "item": item,
            "photos": photos,
            "documents": [self._public_document(org, d, role) for d in self._filter_documents(org, [d for d in docs if not d.get("archived_at")], role, actor_id)],
            "tasks": tasks,
            "client": client,
            "finance": finance,
            "logistics": logistics,
            "customs": customs,
            "crm": crm,
            "sale_package": sale_pack,
            "registration_package": registration_pack,
            "audit": audit[:50],
            "lifecycle": item["lifecycle"],
        }

    def _next_internal_number(self, org: str) -> str:
        n = len(self._bag(org)["vehicles"]) + 1
        return f"A-{n:04d}"

    async def create_vehicle(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        vin = normalize_vin(body.get("vin"))
        allow_ns = bool(body.get("allow_nonstandard_vin") or body.get("resolve_vin_conflict")) and can(role, "vin_override")
        vin_err = validate_vin(vin, allow_nonstandard=allow_ns)
        if vin_err:
            return vin_err
        existing = next((v for v in self._bag(org)["vehicles"] if str(v.get("vin")) == vin), None)
        if existing:
            if not (bool(body.get("resolve_vin_conflict")) and can(role, "vin_override")):
                return {
                    "ok": False,
                    "error": "conflict",
                    "message_ru": "VIN уже есть в базе этой организации. Конфликт может разрешить только директор или администратор.",
                    "existing_id": existing.get("id"),
                }
        status = str(body.get("status") or "INTEREST").upper()
        if status not in STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус автомобиля", "field": "status"}
        manufacturer = str(body.get("manufacturer") or body.get("make") or "").strip()
        model = str(body.get("model") or "").strip()
        auction_url = str(body.get("auction_url") or "").strip()
        if not (manufacturer or model or auction_url):
            return {
                "ok": False,
                "error": "validation",
                "message_ru": "Для быстрого создания укажите марку/модель или ссылку на аукцион",
            }
        item: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "vin": vin,
            "vin_nonstandard": len(vin) != 17,
            "internal_number": str(body.get("internal_number") or "").strip() or self._next_internal_number(org),
            "status": status,
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": actor_id or normalize_role(role),
        }
        for field in VEHICLE_FIELDS:
            if field in {"vin", "status"}:
                continue
            if field in body and body[field] not in (None, ""):
                item[field] = body[field]
        if manufacturer:
            item["manufacturer"] = manufacturer
        if model:
            item["model"] = model
        if auction_url:
            item["auction_url"] = auction_url
        item["year"] = _year(body.get("year"))
        item.setdefault("workspace_id", org)
        if body.get("is_demo") is True:
            item["is_demo"] = True
        for money in ("purchase_price", "buyer_fee", "estimated_market_value", "mileage", "sale_price_expected", "sale_price_actual"):
            if money in item:
                item[money] = _opt_num(item[money])
        saved = await self._persist("vehicle", item)
        self._bag(org)["vehicles"].insert(0, saved)
        src = str(body.get("source") or "WEB").upper()
        if src not in {"WEB", "TELEGRAM", "API"}:
            src = "WEB"
        await self._record_status_history(org, str(saved["id"]), status, actor_id=actor_id, source=src)
        await self._audit(
            organization_id=org,
            action="vehicle_created",
            entity_type="vehicle",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"vin": vin, "status": status},
            summary=f"Создан автомобиль {vin}",
        )
        return {"ok": True, "item": self._public_vehicle(org, saved)}

    async def update_vehicle(self, organization_id: str, vehicle_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "vehicles", vehicle_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль не найден"}
        old = {k: item.get(k) for k in ("vin", "status", "purchase_price", "client_id", "location_current")}
        patch: dict[str, Any] = {}
        if "vin" in body:
            vin = normalize_vin(body.get("vin"))
            allow_ns = bool(body.get("allow_nonstandard_vin")) and can(role, "vin_override")
            vin_err = validate_vin(vin, allow_nonstandard=allow_ns)
            if vin_err:
                return vin_err
            other = next((v for v in self._bag(org)["vehicles"] if str(v.get("vin")) == vin and str(v.get("id")) != str(vehicle_id)), None)
            if other and not (bool(body.get("resolve_vin_conflict")) and can(role, "vin_override")):
                return {"ok": False, "error": "conflict", "message_ru": "VIN уже используется другим автомобилем"}
            patch["vin"] = vin
            patch["vin_nonstandard"] = len(vin) != 17
        if "status" in body:
            status = str(body.get("status") or "").upper()
            if status not in STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус", "field": "status"}
            patch["status"] = status
        if "manufacturer" in body or "make" in body:
            patch["manufacturer"] = str(body.get("manufacturer") or body.get("make") or "").strip()
        for field in VEHICLE_FIELDS:
            if field in {"vin", "status", "manufacturer"}:
                continue
            if field in body:
                patch[field] = body[field]
        if "year" in patch:
            patch["year"] = _year(patch["year"])
        for money in ("purchase_price", "buyer_fee", "estimated_market_value", "mileage", "sale_price_expected", "sale_price_actual"):
            if money in patch:
                patch[money] = _opt_num(patch[money])
        patch["updated_at"] = _now()
        patch["updated_by"] = actor_id or normalize_role(role)
        item.update(patch)
        await self._persist_update("vehicle", vehicle_id, patch)
        if "status" in patch:
            src = str(body.get("source") or "WEB").upper()
            if src not in {"WEB", "TELEGRAM", "API"}:
                src = "WEB"
            await self._record_status_history(org, vehicle_id, str(patch["status"]), actor_id=actor_id, source=src)
        changes = {k: {"old": old.get(k), "new": item.get(k)} for k in old if old.get(k) != item.get(k)}
        action = "vehicle_updated"
        if "status" in changes:
            action = "status_changed"
        elif "vin" in changes:
            action = "vin_changed"
        elif "purchase_price" in changes:
            action = "purchase_price_changed"
        elif "client_id" in changes:
            action = "client_assigned"
        elif "location_current" in changes:
            action = "logistics_status_changed"
        warn = self.status_transition_warning(org, item, str(item.get("status") or "")) if "status" in patch else None
        if warn and body.get("override"):
            await self._audit(
                organization_id=org,
                action="document_guard_override",
                entity_type="vehicle",
                entity_id=vehicle_id,
                role=role,
                actor_id=actor_id,
                old_value={"status": old.get("status")},
                new_value={"status": item.get("status"), "missing": warn.get("missing")},
                summary="document_guard_override",
            )
        await self._audit(
            organization_id=org,
            action=action,
            entity_type="vehicle",
            entity_id=vehicle_id,
            role=role,
            actor_id=actor_id,
            old_value=old,
            new_value={k: item.get(k) for k in old},
            summary=action,
        )
        if "client_id" in changes:
            await self._audit(
                organization_id=org,
                action="ownership_changed",
                entity_type="vehicle",
                entity_id=vehicle_id,
                role=role,
                actor_id=actor_id,
                old_value={"client_id": old.get("client_id")},
                new_value={"client_id": item.get("client_id")},
                summary="Изменена принадлежность / клиент",
            )
        old_st = str(old.get("status") or "")
        new_st = str(item.get("status") or "")
        if old_st != new_st and ("READY_FOR_SALE" in {old_st, new_st}):
            await self._audit(
                organization_id=org,
                action="ready_for_sale_changed",
                entity_type="vehicle",
                entity_id=vehicle_id,
                role=role,
                actor_id=actor_id,
                old_value={"status": old_st},
                new_value={"status": new_st},
                summary="Изменена готовность к продаже",
            )
        out = {"ok": True, "item": self._public_vehicle(org, item)}
        if warn:
            out.update(warn)
        return out

    async def create_expense(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        category = str(body.get("category") or "OTHER").upper()
        if category == "UA_TRANSPORT":
            category = "UA_TRANSPORT"
        logistics_ok = category in LOGISTICS_EXPENSE_IDS and (can(role, "edit") or can(role, "create") or can(role, "finance_write"))
        customs_ok = category in CUSTOMS_EXPENSE_IDS and (can(role, "edit") or can(role, "create") or can(role, "finance_write"))
        if not logistics_ok and not customs_ok:
            denied = require(role, "finance_write")
            if denied:
                return denied
        vehicle_id = str(body.get("vehicle_id") or "").strip()
        shipment_id = str(body.get("shipment_id") or "").strip() or None
        customs_id = str(body.get("customs_id") or "").strip() or None
        if shipment_id:
            ship = self._find(org, "shipments", shipment_id)
            if not ship:
                return {"ok": False, "error": "validation", "message_ru": "Перевозка для расхода не найдена"}
            vehicle_id = vehicle_id or str(ship.get("vehicle_id") or "")
        if customs_id:
            case = self._find(org, "customs_cases", customs_id)
            if not case:
                return {"ok": False, "error": "validation", "message_ru": "Дело растаможки для расхода не найдено"}
            vehicle_id = vehicle_id or str(case.get("vehicle_id") or "")
        if not vehicle_id or not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Расход должен быть привязан к существующему автомобилю"}
        if category not in EXPENSE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестная категория расхода", "field": "category"}
        amount = _opt_num(body.get("amount"))
        if amount is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму", "field": "amount"}
        currency = str(body.get("currency") or "USD").upper()
        rate = _opt_num(body.get("exchange_rate")) or (1.0 if currency in {"USD", "UAH"} else None)
        base = _opt_num(body.get("amount_base_currency"))
        if base is None and rate is not None:
            base = round(amount * rate, 2)
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": str(body.get("workspace_id") or org),
            "vehicle_id": vehicle_id,
            "shipment_id": shipment_id,
            "customs_id": customs_id,
            "category": category,
            "description": str(body.get("description") or "").strip() or None,
            "amount": amount,
            "currency": currency,
            "exchange_rate": rate,
            "amount_base_currency": base,
            "payment_date": body.get("payment_date"),
            "due_at": body.get("due_at") or body.get("payment_due"),
            "is_demo": bool(body.get("is_demo")),
            "counterparty": body.get("counterparty"),
            "payment_method": body.get("payment_method"),
            "payment_status": str(body.get("payment_status") or "paid"),
            "document_id": body.get("document_id"),
            "created_by": actor_id or normalize_role(role),
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("expense", item)
        self._bag(org)["expenses"].insert(0, saved)
        await self._audit(
            organization_id=org,
            action="expense_created",
            entity_type="expense",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"vehicle_id": vehicle_id, "shipment_id": shipment_id, "customs_id": customs_id, "category": category, "amount": amount, "currency": currency},
        )
        if shipment_id:
            await self._audit(
                organization_id=org,
                action="expense_allocated",
                entity_type="shipment",
                entity_id=str(shipment_id),
                role=role,
                actor_id=actor_id,
                new_value={"expense_id": saved["id"], "category": category, "amount": amount},
                summary="Расход распределён на перевозку",
            )
        if customs_id:
            await self._audit(
                organization_id=org,
                action="customs_payment",
                entity_type="customs_case",
                entity_id=customs_id,
                role=role,
                actor_id=actor_id,
                new_value={"category": category, "amount": amount, "currency": currency, "payment_status": item["payment_status"]},
                summary="Платёж по растаможке",
            )
            await self._audit(
                organization_id=org,
                action="customs_payment_added",
                entity_type="customs_case",
                entity_id=customs_id,
                role=role,
                actor_id=actor_id,
                new_value={"expense_id": saved["id"], "category": category, "amount": amount, "payment_status": item["payment_status"]},
                summary="Платёж растаможки добавлен",
            )
            if str(item.get("payment_status") or "") in {"paid", "confirmed"}:
                await self._audit(
                    organization_id=org,
                    action="customs_payment_confirmed",
                    entity_type="customs_case",
                    entity_id=customs_id,
                    role=role,
                    actor_id=actor_id,
                    new_value={"expense_id": saved["id"], "payment_status": item["payment_status"]},
                    summary="Платёж растаможки подтверждён",
                )
        if shipment_id:
            await self._add_event(
                org,
                shipment_id=shipment_id,
                event_type="expense_added",
                description=f"Расход {category} {amount} {currency}",
                role=role,
                actor_id=actor_id,
                source="system",
            )
            if str(body.get("payment_status") or "paid") in {"pending", "planned"}:
                await self._notify(
                    org,
                    ntype="payment_overdue",
                    title="Оплата логистики не закрыта",
                    entity_type="expense",
                    entity_id=str(saved["id"]),
                    shipment_id=shipment_id,
                    vehicle_id=vehicle_id,
                )
        return {"ok": True, "item": saved}

    async def update_expense(self, organization_id: str, expense_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance_write")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "expenses", expense_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Расход не найден"}
        old = {"amount": item.get("amount"), "category": item.get("category"), "payment_status": item.get("payment_status")}
        patch = {k: body[k] for k in ("description", "counterparty", "payment_method", "payment_status", "payment_date", "document_id") if k in body}
        if "category" in body:
            cat = str(body["category"]).upper()
            if cat not in EXPENSE_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестная категория"}
            patch["category"] = cat
        if "amount" in body:
            patch["amount"] = _opt_num(body.get("amount"))
        if "currency" in body:
            patch["currency"] = str(body.get("currency") or "USD").upper()
        if "exchange_rate" in body:
            patch["exchange_rate"] = _opt_num(body.get("exchange_rate"))
        amount = _num(patch.get("amount", item.get("amount")))
        rate = _num(patch.get("exchange_rate", item.get("exchange_rate"))) or 1.0
        patch["amount_base_currency"] = round(amount * rate, 2)
        patch["updated_at"] = _now()
        item.update(patch)
        await self._persist_update("expense", expense_id, patch)
        await self._audit(
            organization_id=org,
            action="expense_updated",
            entity_type="expense",
            entity_id=expense_id,
            role=role,
            actor_id=actor_id,
            old_value=old,
            new_value={"amount": item.get("amount"), "category": item.get("category"), "payment_status": item.get("payment_status")},
        )
        if item.get("customs_id") and str(old.get("payment_status") or "") not in {"paid", "confirmed"} and str(item.get("payment_status") or "") in {"paid", "confirmed"}:
            await self._audit(
                organization_id=org,
                action="customs_payment_confirmed",
                entity_type="customs_case",
                entity_id=str(item.get("customs_id")),
                role=role,
                actor_id=actor_id,
                new_value={"expense_id": expense_id, "payment_status": item.get("payment_status")},
                summary="Платёж растаможки подтверждён",
            )
        return {"ok": True, "item": item}

    async def delete_expense(self, organization_id: str, expense_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not can(role, "finance_write"):
            return require(role, "finance_write") or {"ok": False, "error": "forbidden"}
        if not (can(role, "delete") or normalize_role(role) in {"auto_accountant", "auto_director", "platform_owner"}):
            return {"ok": False, "error": "forbidden", "message_ru": "Удаление расходов недоступно"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "expenses", expense_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Расход не найден"}
        status = str(item.get("payment_status") or "")
        if status in {"paid", "confirmed"}:
            item["payment_status"] = "cancelled"
            item["updated_at"] = _now()
            await self._persist_update("expense", expense_id, {"payment_status": "cancelled", "updated_at": item["updated_at"]})
            await self._audit(
                organization_id=org,
                action="expense_cancelled",
                entity_type="expense",
                entity_id=expense_id,
                role=role,
                actor_id=actor_id,
                old_value={"amount": item.get("amount"), "payment_status": status},
                summary="expense_cancelled",
            )
            return {"ok": True, "void": True, "soft": True, "item": item, "message_ru": "Подтверждённый расход не удаляется. Статус: отменён."}
        item["payment_status"] = "cancelled"
        item["updated_at"] = _now()
        await self._persist_update("expense", expense_id, {"payment_status": "cancelled", "updated_at": item["updated_at"]})
        await self._audit(
            organization_id=org,
            action="expense_cancelled",
            entity_type="expense",
            entity_id=expense_id,
            role=role,
            actor_id=actor_id,
            old_value={"amount": item.get("amount"), "category": item.get("category"), "vehicle_id": item.get("vehicle_id")},
        )
        return {"ok": True, "soft": True, "item": item}

    async def list_expenses(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        q = query or {}
        items = list(self._bag(org)["expenses"])
        vid = (q.get("vehicle_id") or "").strip()
        sid = (q.get("shipment_id") or "").strip()
        cid = (q.get("customs_id") or "").strip()
        if vid:
            items = [e for e in items if str(e.get("vehicle_id")) == vid]
        if sid:
            items = [e for e in items if str(e.get("shipment_id") or "") == sid]
        if cid:
            items = [e for e in items if str(e.get("customs_id") or "") == cid]
        return {"ok": True, "items": items, "total": len(items)}

    async def create_client(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "clients")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        name = str(body.get("name") or body.get("full_name") or "").strip()
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя клиента"}
        tax_id = body.get("tax_id") if body.get("tax_id") not in (None, "") else body.get("tax_number")
        passport_ref = body.get("passport_ref") if body.get("passport_ref") not in (None, "") else body.get("passport")
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "phone": body.get("phone"),
            "telegram": body.get("telegram"),
            "email": body.get("email"),
            "notes": body.get("notes"),
            "assigned_manager_id": body.get("assigned_manager_id"),
            "source": body.get("source"),
            "status": str(body.get("status") or "lead"),
            "passport_ref": passport_ref if can(role, "pii") else None,
            "tax_id": tax_id if can(role, "pii") else None,
            "address": body.get("address") if can(role, "pii") else None,
            "id_number": body.get("id_number") if can(role, "pii") else None,
            "representative": body.get("representative"),
            "is_demo": bool(body.get("is_demo")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("client", item)
        self._bag(org)["clients"].insert(0, saved)
        await self._audit(organization_id=org, action="client_created", entity_type="client", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"name": name})
        return {"ok": True, "item": self._redact_client(saved, role)}

    async def list_clients(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = []
        for c in self._bag(org)["clients"]:
            row = self._redact_client(c, role)
            row["vehicle_ids"] = [v.get("id") for v in self._bag(org)["vehicles"] if str(v.get("client_id")) == str(c.get("id"))]
            row["document_count"] = sum(
                1 for d in self._bag(org)["documents"] if not d.get("archived_at") and str(d.get("client_id") or "") == str(c.get("id"))
            )
            items.append(row)
        return {"ok": True, "items": items}

    async def create_task(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "tasks")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название задачи"}
        vehicle_id = str(body.get("vehicle_id") or "").strip() or None
        shipment_id = str(body.get("shipment_id") or "").strip() or None
        customs_id = str(body.get("customs_id") or "").strip() or None
        if vehicle_id and not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Автомобиль для задачи не найден"}
        if shipment_id:
            ship = self._find(org, "shipments", shipment_id)
            if not ship:
                return {"ok": False, "error": "validation", "message_ru": "Перевозка для задачи не найдена"}
            vehicle_id = vehicle_id or str(ship.get("vehicle_id") or "")
        if customs_id:
            case = self._find(org, "customs_cases", customs_id)
            if not case:
                return {"ok": False, "error": "validation", "message_ru": "Дело растаможки для задачи не найдено"}
            vehicle_id = vehicle_id or str(case.get("vehicle_id") or "")
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "title": title,
            "status": str(body.get("status") or "open"),
            "priority": str(body.get("priority") or "normal"),
            "vehicle_id": vehicle_id,
            "shipment_id": shipment_id,
            "customs_id": customs_id,
            "deal_id": str(body.get("deal_id") or "").strip() or None,
            "client_id": body.get("client_id"),
            "assigned_manager_id": body.get("assigned_manager_id") or body.get("assignee"),
            "due_at": body.get("due_at") or body.get("deadline"),
            "notes": body.get("notes"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("task", item)
        self._bag(org)["tasks"].insert(0, saved)
        await self._audit(organization_id=org, action="task_created", entity_type="task", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"title": title, "vehicle_id": vehicle_id})
        return {"ok": True, "item": saved}

    async def list_tasks(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["tasks"])
        vid = (query or {}).get("vehicle_id") or ""
        sid = (query or {}).get("shipment_id") or ""
        cid = (query or {}).get("customs_id") or ""
        if vid:
            items = [t for t in items if str(t.get("vehicle_id")) == vid]
        if sid:
            items = [t for t in items if str(t.get("shipment_id") or "") == sid]
        if cid:
            items = [t for t in items if str(t.get("customs_id") or "") == cid]
        return {"ok": True, "items": items}

    async def complete_task(self, organization_id: str, task_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "tasks")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "tasks", task_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Задача не найдена"}
        item["status"] = "done"
        item["updated_at"] = _now()
        await self._persist_update("task", task_id, {"status": "done", "updated_at": item["updated_at"]})
        return {"ok": True, "item": item}

    async def create_document(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        dtype = str(body.get("document_type") or body.get("doc_type") or "other")
        if dtype not in DOCUMENT_IDS:
            dtype = "other"
        owner_type = str(body.get("owner_type") or "vehicle")
        if owner_type not in DOCUMENT_OWNERS:
            owner_type = "vehicle"
        vehicle_id = str(body.get("vehicle_id") or "").strip() or None
        shipment_id = str(body.get("shipment_id") or "").strip() or None
        container_id = str(body.get("container_id") or "").strip() or None
        carrier_id = str(body.get("carrier_id") or "").strip() or None
        driver_id = str(body.get("driver_id") or "").strip() or None
        truck_id = str(body.get("truck_id") or "").strip() or None
        vessel_id = str(body.get("vessel_id") or "").strip() or None
        customs_id = str(body.get("customs_id") or "").strip() or None
        if customs_id:
            case = self._find(org, "customs_cases", customs_id)
            if not case:
                return {"ok": False, "error": "validation", "message_ru": "Дело растаможки для документа не найдено"}
            vehicle_id = vehicle_id or str(case.get("vehicle_id") or "")
            if owner_type == "vehicle":
                owner_type = "customs"
        if owner_type == "vehicle" and vehicle_id and not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Автомобиль для документа не найден"}
        file_name = str(body.get("file_name") or body.get("title") or "document").strip()
        extracted = extract_vin_hint(file_name, body.get("notes"), body.get("extracted_vin"), body.get("vin"))
        vehicle = self._find(org, "vehicles", vehicle_id) if vehicle_id else None
        vin_warn = self.vin_link_warning(vehicle, extracted)
        if vin_warn and body.get("relink"):
            return {**vin_warn, "ok": False, "error": "vin_conflict", "message_ru": vin_warn["message_ru"]}
        ocr_draft = None
        if extracted and not body.get("ocr_confirm"):
            ocr_draft = {"vin": extracted, "confirmed": False, "source": "filename"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": str(body.get("workspace_id") or org),
            "document_type": dtype,
            "title": body.get("title") or file_name,
            "file_name": file_name,
            "file_id": body.get("file_id"),
            "owner_type": owner_type,
            "vehicle_id": vehicle_id,
            "client_id": body.get("client_id"),
            "shipment_id": shipment_id,
            "container_id": container_id,
            "carrier_id": carrier_id,
            "driver_id": driver_id,
            "truck_id": truck_id,
            "vessel_id": vessel_id,
            "customs_id": customs_id,
            "deal_id": str(body.get("deal_id") or "").strip() or None,
            "sale_id": body.get("sale_id"),
            "payment_id": body.get("payment_id"),
            "notes": body.get("notes"),
            "archived_at": None,
            "uploaded_by": actor_id or normalize_role(role),
            "created_at": _now(),
            "updated_at": _now(),
            "workflow_status": str(body.get("workflow_status") or ("DRAFT" if body.get("generated") else "")),
            "signature_status": str(body.get("signature_status") or "NOT_REQUIRED"),
            "document_number": body.get("document_number"),
            "issued_by": body.get("issued_by"),
            "issued_date": body.get("issued_date"),
            "valid_until": body.get("valid_until"),
            "finance_verify": str(body.get("finance_verify") or "UNVERIFIED"),
            "generated": bool(body.get("generated")),
            "template_id": body.get("template_id"),
            "ocr_draft": body.get("ocr_draft") or ocr_draft,
            "extracted_vin": extracted,
            "source": str(body.get("source") or "WEB").upper(),
            "assigned_to": body.get("assigned_to") or body.get("responsible"),
            "category": body.get("category"),
            "legal_disclaimer": body.get("legal_disclaimer"),
        }
        saved = await self._persist("document", item)
        self._bag(org)["documents"].insert(0, saved)
        await self._audit(organization_id=org, action="document_uploaded", entity_type="document", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"vehicle_id": vehicle_id, "customs_id": customs_id, "document_type": dtype, "file_name": file_name, "source": saved.get("source")})
        if shipment_id or vehicle_id:
            await self._audit(
                organization_id=org,
                action="document_linked",
                entity_type="document",
                entity_id=str(saved["id"]),
                role=role,
                actor_id=actor_id,
                new_value={"vehicle_id": vehicle_id, "shipment_id": shipment_id, "document_type": dtype},
                summary="Документ привязан",
            )
        if customs_id:
            await self._audit(organization_id=org, action="customs_document", entity_type="customs_case", entity_id=customs_id, role=role, actor_id=actor_id, new_value={"document_type": dtype}, summary="Документ по растаможке")
        out = {"ok": True, "item": saved}
        if vin_warn:
            out.update(vin_warn)
        issues = self.validate_document_record(org, saved)
        if issues:
            out["validation"] = issues
        return out

    async def list_documents(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = [d for d in self._bag(org)["documents"] if not d.get("archived_at") or (query or {}).get("include_archived")]
        q = query or {}
        for key in ("vehicle_id", "shipment_id", "container_id", "carrier_id", "driver_id", "truck_id", "customs_id", "client_id", "deal_id"):
            val = q.get(key) or ""
            if val:
                items = [d for d in items if str(d.get(key) or "") == val]
        if q.get("type") or q.get("document_type"):
            dtype = q.get("type") or q.get("document_type") or ""
            items = [d for d in items if str(d.get("document_type") or "") == dtype]
        if q.get("status") or q.get("workflow_status"):
            st = q.get("status") or q.get("workflow_status") or ""
            items = [d for d in items if str(d.get("workflow_status") or "") == st]
        if q.get("category"):
            cat = q["category"]
            items = [d for d in items if str(d.get("category") or "") == cat]
        if q.get("vin"):
            needle = q["vin"].strip().upper()
            vids = {str(v.get("id")) for v in self._bag(org)["vehicles"] if needle in str(v.get("vin") or "").upper()}
            items = [d for d in items if str(d.get("vehicle_id") or "") in vids or needle in str(d.get("extracted_vin") or "").upper()]
        search = (q.get("q") or "").strip().upper()
        if search:
            items = [
                d
                for d in items
                if search in " ".join(str(d.get(k) or "") for k in ("title", "file_name", "document_type", "document_number", "notes")).upper()
            ]
        items = self._filter_documents(org, items, role, actor_id)
        return {"ok": True, "items": items, "total": len(items)}

    async def delete_document(self, organization_id: str, document_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "documents") and (can(role, "delete") or can(role, "admin"))):
            return {"ok": False, "error": "forbidden", "message_ru": "Удаление документов доступно директору или администратору"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "documents", document_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        if item.get("archived_at"):
            self._bag(org)["documents"] = [d for d in self._bag(org)["documents"] if str(d.get("id")) != str(document_id)]
            await self._persist_delete("document", document_id)
            await self._audit(organization_id=org, action="document_deleted", entity_type="document", entity_id=document_id, role=role, actor_id=actor_id, old_value={"file_name": item.get("file_name"), "vehicle_id": item.get("vehicle_id")})
            return {"ok": True, "deleted": True}
        item["archived_at"] = _now()
        item["updated_at"] = _now()
        await self._persist_update("document", document_id, {"archived_at": item["archived_at"], "updated_at": item["updated_at"]})
        await self._audit(organization_id=org, action="document_deleted", entity_type="document", entity_id=document_id, role=role, actor_id=actor_id, old_value={"file_name": item.get("file_name"), "soft": True})
        return {"ok": True, "deleted": True, "soft": True}

    async def restore_document(self, organization_id: str, document_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "documents") and (can(role, "delete") or can(role, "admin") or can(role, "edit"))):
            return {"ok": False, "error": "forbidden", "message_ru": "Восстановление документов недоступно"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "documents", document_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        item["archived_at"] = None
        item["updated_at"] = _now()
        await self._persist_update("document", document_id, {"archived_at": None, "updated_at": item["updated_at"]})
        return {"ok": True, "item": item}

    async def update_document(self, organization_id: str, document_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "documents", document_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        old = {k: item.get(k) for k in ("title", "file_name", "document_type", "file_id", "vehicle_id", "workflow_status", "signature_status", "notes")}
        fields = (
            "title",
            "file_name",
            "notes",
            "document_type",
            "file_id",
            "document_number",
            "issued_by",
            "issued_date",
            "valid_until",
            "assigned_to",
            "category",
            "client_id",
            "deal_id",
            "payment_id",
            "shipment_id",
            "container_id",
        )
        patch = {k: body[k] for k in fields if k in body}
        if "vehicle_id" in body:
            new_vid = str(body.get("vehicle_id") or "").strip() or None
            vehicle = self._find(org, "vehicles", new_vid) if new_vid else None
            extracted = str(item.get("extracted_vin") or extract_vin_hint(item.get("file_name"), item.get("notes")) or "")
            warn = self.vin_link_warning(vehicle, extracted or None)
            if warn and not body.get("confirm_relink"):
                return {**warn, "ok": False, "error": "vin_conflict"}
            if str(item.get("vehicle_id") or "") != str(new_vid or ""):
                patch["vehicle_id"] = new_vid
        if "file_id" in patch and item.get("file_id") and patch["file_id"] != item.get("file_id"):
            patch["previous_file_id"] = item.get("file_id")
        if any(k in body for k in ("workflow_status", "signature_status", "finance_verify")):
            status_res = await self.update_document_status(org, document_id, body, role, actor_id)
            if not status_res.get("ok"):
                return status_res
            item = self._find(org, "documents", document_id) or item
        patch["updated_at"] = _now()
        item.update(patch)
        await self._persist_update("document", document_id, patch)
        action = "document_replaced" if "file_id" in patch else "document_renamed" if "title" in patch or "file_name" in patch else "document_type_changed" if "document_type" in patch else "document_linked" if "vehicle_id" in patch else "document_updated"
        await self._audit(organization_id=org, action=action, entity_type="document", entity_id=document_id, role=role, actor_id=actor_id, old_value=old, new_value={k: item.get(k) for k in old})
        out = {"ok": True, "item": self._public_document(org, item, role)}
        issues = self.validate_document_record(org, item)
        if issues:
            out["validation"] = issues
        return out

    async def create_photo(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "photos")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        vehicle_id = str(body.get("vehicle_id") or "").strip()
        shipment_id = str(body.get("shipment_id") or "").strip() or None
        if shipment_id:
            ship = self._find(org, "shipments", shipment_id)
            if not ship:
                return {"ok": False, "error": "validation", "message_ru": "Перевозка для фото не найдена"}
            vehicle_id = vehicle_id or str(ship.get("vehicle_id") or "")
        if not vehicle_id or not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Фото должно быть привязано к автомобилю"}
        category = str(body.get("category") or "OTHER").upper()
        if category not in PHOTO_IDS:
            category = "OTHER"
        file_id = str(body.get("file_id") or "").strip()
        if not file_id:
            return {"ok": False, "error": "validation", "message_ru": "Сначала загрузите файл"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "vehicle_id": vehicle_id,
            "shipment_id": shipment_id,
            "category": category,
            "file_id": file_id,
            "file_name": body.get("file_name"),
            "location": body.get("location"),
            "captured_at": body.get("captured_at") or _now(),
            "is_cover": bool(body.get("is_cover")),
            "uploaded_by": actor_id or normalize_role(role),
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("photo", item)
        self._bag(org)["photos"].insert(0, saved)
        if item["is_cover"]:
            await self.update_vehicle(org, vehicle_id, {"cover_photo_id": file_id}, role, actor_id)
        return {"ok": True, "item": saved}

    async def list_photos(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["photos"])
        vid = (query or {}).get("vehicle_id") or ""
        if vid:
            items = [p for p in items if str(p.get("vehicle_id")) == vid]
        return {"ok": True, "items": items}

    async def delete_photo(self, organization_id: str, photo_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "photos") and (can(role, "delete") or can(role, "admin") or can(role, "edit"))):
            return {"ok": False, "error": "forbidden", "message_ru": "Недостаточно прав для удаления фото"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "photos", photo_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Фото не найдено"}
        self._bag(org)["photos"] = [p for p in self._bag(org)["photos"] if str(p.get("id")) != str(photo_id)]
        await self._persist_delete("photo", photo_id)
        return {"ok": True, "deleted": True}

    async def set_cover_photo(self, organization_id: str, photo_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "photos")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        photo = self._find(org, "photos", photo_id)
        if not photo:
            return {"ok": False, "error": "not_found", "message_ru": "Фото не найдено"}
        for p in self._bag(org)["photos"]:
            if str(p.get("vehicle_id")) == str(photo.get("vehicle_id")):
                p["is_cover"] = str(p.get("id")) == str(photo_id)
        return await self.update_vehicle(org, str(photo.get("vehicle_id")), {"cover_photo_id": photo.get("file_id")}, role)

    async def upload_file(
        self,
        organization_id: str,
        *,
        filename: str,
        mime_type: str | None,
        data: bytes,
        entity_type: str | None,
        entity_id: str | None,
        role: str | None,
        uploaded_by: str | None = None,
        as_photo: bool = False,
        photo_category: str | None = None,
        document_type: str | None = None,
        customs_id: str | None = None,
    ) -> dict[str, Any]:
        need = "photos" if as_photo else "documents"
        denied = require(role, need)
        if denied:
            return denied
        err = validate_upload(filename, mime_type)
        if err:
            return err
        if not data:
            return {"ok": False, "error": "validation", "message_ru": "Файл пустой"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        file_id = str(uuid.uuid4())
        path = write_bytes(org, file_id, data)
        meta = {
            "id": file_id,
            "organization_id": org,
            "tenant_id": org,
            "file_name": filename,
            "mime_type": mime_type,
            "storage_path": path,
            "size_bytes": len(data),
            "uploaded_by": uploaded_by or normalize_role(role),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("file", meta)
        self._bag(org)["files"].insert(0, saved)
        extra: dict[str, Any] = {}
        if as_photo and entity_id:
            extra = await self.create_photo(
                org,
                {
                    "vehicle_id": entity_id if entity_type in (None, "vehicle") else None,
                    "shipment_id": entity_id if entity_type == "shipment" else None,
                    "file_id": file_id,
                    "file_name": filename,
                    "category": photo_category or "OTHER",
                },
                role,
                uploaded_by,
            )
        elif entity_type in DOCUMENT_OWNERS or entity_type == "vehicle":
            extra = await self.create_document(
                org,
                {
                    "file_id": file_id,
                    "file_name": filename,
                    "owner_type": entity_type or "vehicle",
                    "vehicle_id": entity_id if (entity_type or "vehicle") == "vehicle" else None,
                    "client_id": entity_id if entity_type == "client" else None,
                    "shipment_id": entity_id if entity_type == "shipment" else None,
                    "container_id": entity_id if entity_type == "container" else None,
                    "carrier_id": entity_id if entity_type == "carrier" else None,
                    "driver_id": entity_id if entity_type == "driver" else None,
                    "truck_id": entity_id if entity_type == "truck" else None,
                    "vessel_id": entity_id if entity_type == "vessel" else None,
                    "document_type": document_type or "other",
                    "customs_id": customs_id,
                },
                role,
                uploaded_by,
            )
        return {"ok": True, "item": saved, "linked": extra.get("item") if isinstance(extra, dict) else None}

    async def list_files(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": list(self._bag(org)["files"])}

    async def file_content(self, organization_id: str, file_id: str, role: str | None) -> tuple[dict[str, Any] | None, bytes | None]:
        denied = require(role, "get")
        if denied:
            return denied, None
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        meta = self._find(org, "files", file_id)
        if not meta:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}, None
        data = read_bytes(str(meta.get("storage_path") or ""))
        if data is None:
            return {"ok": False, "error": "not_found", "message_ru": "Файл отсутствует на диске"}, None
        return None, data

    async def list_audit(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "audit")
        if denied:
            denied_view = require(role, "list")
            if denied_view:
                return denied_view
            # managers see vehicle-scoped audit via profile; full log is director/admin/accountant
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["audit"])
        q = query or {}
        if q.get("entity_id"):
            items = [a for a in items if str(a.get("entity_id")) == q["entity_id"]]
        if q.get("entity_type"):
            items = [a for a in items if str(a.get("entity_type")) == q["entity_type"]]
        if not can(role, "audit"):
            items = [a for a in items if str(a.get("entity_type")) == "vehicle"]
        return {"ok": True, "items": items[:200]}

    async def reports(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        q = query or {}
        if q.get("report") or q.get("type"):
            return await self.reports_desk(organization_id, role, q)
        denied = require(role, "reports")
        if denied:
            return denied
        dash = await self.dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        by_status: dict[str, int] = {}
        for v in self._bag(org)["vehicles"]:
            st = str(v.get("status") or "")
            by_status[st] = by_status.get(st, 0) + 1
        desk = await self.reports_desk(organization_id, role, {"report": "funnel"})
        return {
            "ok": True,
            "from_records": True,
            "dashboard": dash,
            "by_status": by_status,
            "funnel": desk.get("items") if desk.get("ok") else [],
            "managers": self._manager_metrics(org),
            "employee_scoring": False,
            "types": desk.get("types"),
            "note_ru": "Отчёт строится только по фактическим записям. Пустые цифры означают отсутствие данных, а не нулевой рынок.",
        }

    async def settings(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        self._ensure_document_templates(org)
        return {
            "ok": True,
            "organization_id": org,
            "private": True,
            "roles": self.roles(),
            "catalogs": self.catalogs(),
            "telegram": self.telegram(),
            "technical": {
                "api": "/api/auto-ops/v1",
                "persistence": "postgres+memory_fallback",
                "public_routes": False,
                "base_currency": "USD",
            },
            "can_admin": can(role, "admin"),
            "company": self._company_profile(org),
            "document_templates": self._bag(org)["document_templates"][:80] if can(role, "list") else [],
            "logistics": {
                "delay_thresholds": self._thresholds(org),
                "tracking_policy": self.catalogs().get("tracking_policy"),
                "providers": [self._public_provider(p) for p in self._bag(org).get("logistics_providers") or []],
                "policy": self._logistics_policy(org),
            },
        }


_SVC: AutoOpsService | None = None


def get_auto_ops_service() -> AutoOpsService:
    global _SVC
    if _SVC is None:
        _SVC = AutoOpsService()
    return _SVC


def reset_auto_ops_for_tests() -> None:
    global _SVC
    _SVC = None
    reset_telegram_runtime_for_tests()

"""AUTO 1.3 CRM / sales / receipts / reports.

Mixin for AutoOpsService. Reuses AUTO 1.0 clients, expenses, documents, tasks, audit.
No employee scoring. No hard delete of confirmed payments or completed sales.
PII is redacted in the service layer, not only in the UI.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from typing import Any

from services.auto_ops.catalog import KPI_STATUS_GROUPS
from services.auto_ops.documents_catalog import SALE_PACKAGE_ITEMS
from services.auto_ops.crm_catalog import (
    CLOSED_FINANCIAL,
    CONFIRMED_RECEIPT,
    CRM_TABS,
    DEAL_STAGE_IDS,
    DEAL_STAGE_LABELS,
    IDENTITY_DOC_TYPES,
    IN_STOCK_STATUSES,
    IN_TRANSIT_STATUSES,
    NEXT_STAGE,
    PII_FIELDS,
    RECEIPT_KIND_IDS,
    RECEIPT_KIND_LABELS,
    RECEIPT_STATUS_IDS,
    REPORT_TYPES,
    RESERVATION_LABELS,
    RESERVATION_STATUS_IDS,
    SALE_LABELS,
    SALE_STATUS_IDS,
    DEAL_STAGES,
    pipeline_for_stage,
    profit_snapshot,
)
from services.auto_ops.rbac import can, normalize_role, require

CRM_BAG_KEYS = ("deals", "reservations", "sales", "receipts")

DEAL_FIELDS = (
    "client_id",
    "vehicle_id",
    "stage",
    "assigned_manager_id",
    "sale_price",
    "currency",
    "notes",
    "source",
    "is_demo",
    "due_at",
    "payment_due",
)


def _str(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _day(value: Any) -> date | None:
    raw = _str(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


class AutoOpsCrmMixin:
    """Clients, deals, reservations, sales, receipts, reports, search."""

    def _redact_client(self, item: dict[str, Any], role: str | None) -> dict[str, Any]:
        out = dict(item)
        if not can(role, "pii"):
            for field in PII_FIELDS:
                if out.get(field):
                    out[field] = "***"
            out["pii_restricted"] = True
            if not can(role, "clients"):
                out["phone"] = "***" if out.get("phone") else None
                out["email"] = "***" if out.get("email") else None
                out["telegram"] = "***" if out.get("telegram") else None
                out["address"] = "***"
        return out

    def _deal_receipts(self, org: str, deal_id: str) -> list[dict[str, Any]]:
        return [r for r in self._bag(org)["receipts"] if str(r.get("deal_id") or "") == str(deal_id)]

    def _payment_rollup(self, org: str, deal: dict[str, Any]) -> dict[str, Any]:
        paid = pending = refunded = 0.0
        lines: list[dict[str, Any]] = []
        by_currency: dict[str, float] = {}
        for rec in self._deal_receipts(org, str(deal.get("id"))):
            status = str(rec.get("status") or "")
            kind = str(rec.get("kind") or "")
            if status in {"cancelled", "void"}:
                continue
            base = rec.get("amount_base_currency")
            amt = _num(base) if base not in (None, "") else _num(rec.get("amount"))
            cur = str(rec.get("currency") or deal.get("currency") or "USD")
            if kind == "REFUND":
                refunded += amt
            elif status in CONFIRMED_RECEIPT:
                paid += amt
                by_currency[cur] = by_currency.get(cur, 0.0) + amt
            elif status != "refunded":
                pending += amt
            lines.append(rec)
        price = _num(deal.get("sale_price"))
        net_paid = round(max(paid - refunded, 0), 2)
        outstanding = round(max(price - net_paid, 0), 2) if price else round(pending, 2)
        return {
            "paid": net_paid,
            "pending": round(pending, 2),
            "refunded": round(refunded, 2),
            "outstanding": outstanding,
            "sale_price": price or None,
            "currency": str(deal.get("currency") or "USD"),
            "by_currency": {k: round(v, 2) for k, v in by_currency.items()},
            "from_records": True,
            "lines": lines,
        }

    def _expire_reservations(self, org: str) -> None:
        today = datetime.now(timezone.utc).date()
        for res in self._bag(org)["reservations"]:
            if str(res.get("status") or "").upper() != "ACTIVE":
                continue
            exp = _day(res.get("expires_at"))
            if exp and exp < today:
                res["status"] = "EXPIRED"
                res["updated_at"] = self._now()

    def _active_reservation(self, org: str, vehicle_id: str) -> dict[str, Any] | None:
        self._expire_reservations(org)
        for res in self._bag(org)["reservations"]:
            if str(res.get("vehicle_id")) != str(vehicle_id):
                continue
            if str(res.get("status") or "").upper() == "ACTIVE":
                return res
        return None

    def _completed_sale(self, org: str, vehicle_id: str) -> dict[str, Any] | None:
        for sale in self._bag(org)["sales"]:
            if str(sale.get("vehicle_id")) == str(vehicle_id) and str(sale.get("status") or "").upper() == "COMPLETED":
                return sale
        return None

    def _crm_notify(self, org: str, *, ntype: str, title: str, entity_type: str, entity_id: str, vehicle_id: str | None = None) -> None:
        day = str(self._now())[:10]
        key = f"{ntype}:{entity_type}:{entity_id}:{day}"
        for existing in self._bag(org)["notifications"]:
            if existing.get("dedupe_key") == key:
                return
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "notification_type": ntype,
            "title": title,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "vehicle_id": vehicle_id,
            "dedupe_key": key,
            "channel": "in_app",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        # persist best-effort via existing kind
        self._bag(org)["notifications"].insert(0, item)
        notify = getattr(self, "notify_telegram_staff", None)
        if notify:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    notify(org, title=title, entity_type=entity_type, entity_id=entity_id, vehicle_id=vehicle_id)
                )
            except RuntimeError:
                pass

    def _public_deal(self, org: str, deal: dict[str, Any], role: str | None) -> dict[str, Any]:
        client = self._find(org, "clients", str(deal.get("client_id") or "")) if deal.get("client_id") else None
        vehicle = self._find(org, "vehicles", str(deal.get("vehicle_id") or "")) if deal.get("vehicle_id") else None
        stage = str(deal.get("stage") or "LEAD").upper()
        rollup = self._payment_rollup(org, deal)
        if not can(role, "finance") and not can(role, "clients"):
            rollup = {"restricted": True, "message_ru": "Суммы доступны менеджеру, директору и бухгалтеру."}
        cost = self._vehicle_invested(org, str(vehicle.get("id"))) if vehicle and can(role, "finance") else None
        revenue = rollup.get("paid") if isinstance(rollup.get("paid"), (int, float)) else 0
        profit = profit_snapshot(cost=cost or 0, revenue=float(revenue or 0)) if can(role, "finance") else {"restricted": True}
        reservation = next((r for r in self._bag(org)["reservations"] if str(r.get("deal_id")) == str(deal.get("id"))), None)
        sale = next((s for s in self._bag(org)["sales"] if str(s.get("deal_id")) == str(deal.get("id"))), None)
        client_pub = self._redact_client(client, role) if client else None
        next_id = NEXT_STAGE.get(stage, stage)
        todos: list[str] = []
        if stage in {"LEAD", "CONTACT"} and not deal.get("vehicle_id"):
            todos.append("Выбрать автомобиль")
        if stage in {"VEHICLE_SELECTED"}:
            todos.append("Оформить резерв")
        if rollup.get("outstanding") and stage not in {"COMPLETED", "CANCELLED", "LOST"}:
            todos.append("Закрыть остаток оплаты")
        if not todos and next_id != stage:
            todos.append(f"Следующий этап: {DEAL_STAGE_LABELS.get(next_id, next_id)}")
        answers = {
            "client": (client_pub or {}).get("name") or "—",
            "vehicle": self._vehicle_title(vehicle) if vehicle else "—",
            "stage": DEAL_STAGE_LABELS.get(stage, stage),
            "how_much": rollup.get("sale_price") if not rollup.get("restricted") else None,
            "paid": rollup.get("paid") if not rollup.get("restricted") else None,
            "owed": rollup.get("outstanding") if not rollup.get("restricted") else None,
            "documents": self._deal_doc_summary(org, deal, role),
            "next": DEAL_STAGE_LABELS.get(next_id, next_id),
            "responsible": deal.get("assigned_manager_id") or (client or {}).get("assigned_manager_id") or "—",
        }
        return {
            **deal,
            "stage_ru": DEAL_STAGE_LABELS.get(stage, stage),
            "client_name": (client_pub or {}).get("name") or "",
            "vehicle_title": self._vehicle_title(vehicle) if vehicle else "",
            "vin": (vehicle or {}).get("vin"),
            "pipeline": pipeline_for_stage(stage),
            "payments": rollup,
            "profit": profit,
            "reservation": reservation,
            "sale": sale,
            "client": client_pub,
            "answers": answers,
            "todo": todos,
            "document_count": answers.get("documents"),
        }

    def _deal_doc_summary(self, org: str, deal: dict[str, Any], role: str | None) -> str:
        cid = str(deal.get("client_id") or "")
        vid = str(deal.get("vehicle_id") or "")
        docs = [
            d
            for d in self._bag(org)["documents"]
            if not d.get("archived_at")
            and (str(d.get("client_id") or "") == cid or str(d.get("vehicle_id") or "") == vid or str(d.get("deal_id") or "") == str(deal.get("id")))
        ]
        if not docs:
            return "Документов 0/0"
        if vid and hasattr(self, "_eval_package"):
            vehicle = self._find(org, "vehicles", vid)
            pack = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS) if vehicle else None
            if pack:
                return f"Документы {pack.get('present_count')}/{pack.get('required_count')}"
        n = len(docs)
        return f"{n} документ(ов)"

    def vehicle_crm_block(self, org: str, vehicle_id: str, role: str | None) -> dict[str, Any]:
        deals = [d for d in self._bag(org)["deals"] if str(d.get("vehicle_id")) == str(vehicle_id)]
        deals.sort(key=lambda d: str(d.get("updated_at") or ""), reverse=True)
        current = next((d for d in deals if str(d.get("stage") or "") not in {"COMPLETED", "CANCELLED", "LOST"}), deals[0] if deals else None)
        if not current:
            return {"deal": None, "deals": [], "message_ru": "Сделка ещё не создана."}
        return {"deal": self._public_deal(org, current, role), "deals": [self._public_deal(org, d, role) for d in deals]}

    async def get_client(self, organization_id: str, client_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "clients") if not can(role, "finance") else None
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "clients", client_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Клиент не найден"}
        deals = [self._public_deal(org, d, role) for d in self._bag(org)["deals"] if str(d.get("client_id")) == str(client_id)]
        return {"ok": True, "item": self._redact_client(item, role), "deals": deals}

    async def update_client(self, organization_id: str, client_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "clients")
        if denied:
            return denied
        if any(k in body for k in PII_FIELDS) and not can(role, "pii"):
            return {"ok": False, "error": "forbidden", "message_ru": "Паспорт, ИНН и адрес доступны директору и администратору"}
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "clients", client_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Клиент не найден"}
        old_manager = item.get("assigned_manager_id")
        if "full_name" in body and "name" not in body:
            body = {**body, "name": body.get("full_name")}
        if "tax_number" in body and "tax_id" not in body:
            body = {**body, "tax_id": body.get("tax_number")}
        if "passport" in body and "passport_ref" not in body:
            body = {**body, "passport_ref": body.get("passport")}
        fields = ("name", "phone", "telegram", "email", "notes", "assigned_manager_id", "source", "status", "representative", *PII_FIELDS)
        patch = {k: body[k] for k in fields if k in body}
        patch["updated_at"] = self._now()
        item.update(patch)
        await self._persist_update("client", client_id, patch)
        action = "manager_reassigned" if "assigned_manager_id" in patch and patch.get("assigned_manager_id") != old_manager else "client_edited"
        await self._audit(organization_id=org, action=action, entity_type="client", entity_id=client_id, role=role, actor_id=actor_id, new_value={k: patch.get(k) for k in patch if k != "updated_at"}, summary=action)
        return {"ok": True, "item": self._redact_client(item, role)}

    async def list_deals(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._expire_reservations(org)
        q = query or {}
        items = [self._public_deal(org, d, role) for d in self._bag(org)["deals"]]
        tab = (q.get("tab") or "all").strip()
        tab_def = next((t for t in CRM_TABS if t["id"] == tab), CRM_TABS[0])
        if tab_def.get("stages"):
            wanted = set(tab_def["stages"])
            items = [d for d in items if str(d.get("stage")) in wanted]
        if q.get("stage"):
            items = [d for d in items if str(d.get("stage")) == q["stage"].upper()]
        if q.get("manager"):
            items = [d for d in items if str(d.get("assigned_manager_id") or "") == q["manager"]]
        if q.get("vehicle") or q.get("vehicle_id"):
            vid = q.get("vehicle") or q.get("vehicle_id") or ""
            items = [d for d in items if str(d.get("vehicle_id") or "") == vid]
        if q.get("vin"):
            needle = q["vin"].strip().upper()
            items = [d for d in items if needle in str(d.get("vin") or "").upper()]
        if q.get("status"):
            items = [d for d in items if str(d.get("stage")) == q["status"].upper()]
        if q.get("currency"):
            items = [d for d in items if str(d.get("currency") or "").upper() == q["currency"].upper()]
        if q.get("date") or q.get("date_from"):
            day = (q.get("date") or q.get("date_from") or "")[:10]
            items = [d for d in items if str(d.get("created_at") or "")[:10] >= day]
        search = (q.get("q") or "").strip().upper()
        if search:
            items = [d for d in items if search in " ".join(str(d.get(k) or "") for k in ("client_name", "vehicle_title", "vin", "stage")).upper()]
        counts = {t["id"]: 0 for t in CRM_TABS}
        all_pub = [self._public_deal(org, d, role) for d in self._bag(org)["deals"]]
        for t in CRM_TABS:
            if t.get("stages"):
                wanted = set(t["stages"])
                counts[t["id"]] = sum(1 for d in all_pub if str(d.get("stage")) in wanted)
            else:
                counts[t["id"]] = len(all_pub)
        return {"ok": True, "items": items, "total": len(items), "counts": counts, "tabs": CRM_TABS}

    async def get_deal(self, organization_id: str, deal_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        deal = self._find(org, "deals", deal_id)
        if not deal:
            return {"ok": False, "error": "not_found", "message_ru": "Сделка не найдена"}
        pub = self._public_deal(org, deal, role)
        tasks = [t for t in self._bag(org)["tasks"] if str(t.get("deal_id") or "") == str(deal_id) or str(t.get("client_id") or "") == str(deal.get("client_id") or "")]
        docs = [d for d in self._bag(org)["documents"] if str(d.get("deal_id") or "") == str(deal_id) or str(d.get("client_id") or "") == str(deal.get("client_id") or "")]
        return {"ok": True, "item": pub, "tasks": tasks, "documents": docs}

    async def create_deal(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "clients") if not can(role, "create") else None
        if denied:
            return denied
        if not (can(role, "create") or can(role, "clients")):
            return require(role, "create")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        client_id = _str(body.get("client_id"))
        if not client_id or not self._find(org, "clients", client_id):
            return {"ok": False, "error": "validation", "message_ru": "Сделка должна быть привязана к клиенту"}
        vehicle_id = _str(body.get("vehicle_id")) or None
        if vehicle_id and not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Автомобиль не найден"}
        if vehicle_id and self._completed_sale(org, vehicle_id):
            return {"ok": False, "error": "conflict", "message_ru": "Автомобиль уже продан"}
        stage = _str(body.get("stage") or "LEAD").upper()
        if stage not in DEAL_STAGE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный этап сделки", "field": "stage"}
        item: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "client_id": client_id,
            "vehicle_id": vehicle_id,
            "stage": stage,
            "currency": _str(body.get("currency") or "USD").upper() or "USD",
            "assigned_manager_id": body.get("assigned_manager_id"),
            "sale_price": body.get("sale_price"),
            "notes": body.get("notes"),
            "source": body.get("source") or "crm",
            "is_demo": bool(body.get("is_demo")),
            "due_at": body.get("due_at") or body.get("payment_due"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
        }
        saved = await self._persist("deal", item)
        self._bag(org)["deals"].insert(0, saved)
        action = "lead_created" if stage == "LEAD" else "deal_created"
        await self._audit(organization_id=org, action=action, entity_type="deal", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"client_id": client_id, "stage": stage}, summary=action)
        self._crm_notify(org, ntype="deal_created", title="Создана сделка", entity_type="deal", entity_id=str(saved["id"]), vehicle_id=vehicle_id)
        return {"ok": True, "item": self._public_deal(org, saved, role)}

    async def update_deal(self, organization_id: str, deal_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "edit") or can(role, "clients")):
            return require(role, "edit")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "deals", deal_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Сделка не найдена"}
        old_stage = str(item.get("stage") or "")
        old_manager = item.get("assigned_manager_id")
        patch: dict[str, Any] = {}
        if "stage" in body:
            stage = _str(body.get("stage")).upper()
            if stage not in DEAL_STAGE_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный этап сделки", "field": "stage"}
            patch["stage"] = stage
        for field in DEAL_FIELDS:
            if field in body and field not in {"stage"}:
                patch[field] = body[field]
        patch["updated_at"] = self._now()
        item.update(patch)
        await self._persist_update("deal", deal_id, patch)
        action = "deal_updated"
        if patch.get("stage") and patch["stage"] != old_stage:
            action = "lead_stage_changed" if old_stage == "LEAD" or patch["stage"] in {"CONTACT", "LEAD"} else "deal_stage_changed"
            self._crm_notify(org, ntype="deal_stage_changed", title=f"Этап: {DEAL_STAGE_LABELS.get(patch['stage'], patch['stage'])}", entity_type="deal", entity_id=deal_id, vehicle_id=str(item.get("vehicle_id") or "") or None)
        elif "assigned_manager_id" in patch and patch.get("assigned_manager_id") != old_manager:
            action = "manager_reassigned"
        await self._audit(organization_id=org, action=action, entity_type="deal", entity_id=deal_id, role=role, actor_id=actor_id, old_value={"stage": old_stage}, new_value=patch, summary=action)
        out = {"ok": True, "item": self._public_deal(org, item, role)}
        if str(item.get("stage") or "") == "COMPLETED":
            warn = self.deal_close_warning(org, item)
            if warn:
                out.update(warn)
                if body.get("override"):
                    await self._audit(organization_id=org, action="deal_close_override", entity_type="deal", entity_id=deal_id, role=role, actor_id=actor_id, new_value={"missing": warn.get("missing")}, summary="deal_close_override")
        return out

    async def create_reservation(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "create") or can(role, "clients")):
            return require(role, "create")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle_id = _str(body.get("vehicle_id"))
        client_id = _str(body.get("client_id"))
        deal_id = _str(body.get("deal_id")) or None
        vehicle = self._find(org, "vehicles", vehicle_id) if vehicle_id else None
        if not vehicle or not client_id:
            return {"ok": False, "error": "validation", "message_ru": "Резерв требует клиента и автомобиль"}
        if str(vehicle.get("status") or "") == "SOLD" or self._completed_sale(org, vehicle_id):
            return {"ok": False, "error": "conflict", "message_ru": "Нельзя резервировать проданный автомобиль"}
        existing = self._active_reservation(org, vehicle_id)
        if existing:
            if not (body.get("override") and (can(role, "admin") or can(role, "delete"))):
                return {"ok": False, "error": "conflict", "message_ru": "Автомобиль уже в резерве. Снять резерв может директор (override)."}
            existing["status"] = "CANCELLED"
            existing["override_reason"] = body.get("override_reason") or "override"
            existing["updated_at"] = self._now()
            await self._audit(organization_id=org, action="reservation_overridden", entity_type="reservation", entity_id=str(existing["id"]), role=role, actor_id=actor_id, new_value={"reason": existing["override_reason"]}, summary="reservation_overridden")
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "vehicle_id": vehicle_id,
            "client_id": client_id,
            "deal_id": deal_id,
            "status": "ACTIVE",
            "expires_at": body.get("expires_at"),
            "notes": body.get("notes"),
            "is_demo": bool(body.get("is_demo")),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
        }
        saved = await self._persist("reservation", item)
        self._bag(org)["reservations"].insert(0, saved)
        vehicle["status"] = "RESERVED"
        vehicle["client_id"] = client_id
        vehicle["updated_at"] = self._now()
        await self._persist_update("vehicle", vehicle_id, {"status": "RESERVED", "client_id": client_id, "updated_at": vehicle["updated_at"]})
        if deal_id:
            deal = self._find(org, "deals", deal_id)
            if deal:
                deal["stage"] = "RESERVED"
                deal["vehicle_id"] = vehicle_id
                deal["updated_at"] = self._now()
                await self._persist_update("deal", deal_id, {"stage": "RESERVED", "vehicle_id": vehicle_id, "updated_at": deal["updated_at"]})
        await self._audit(organization_id=org, action="reservation_created", entity_type="reservation", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"vehicle_id": vehicle_id, "client_id": client_id}, summary="reservation_created")
        self._crm_notify(org, ntype="reservation_created", title="Автомобиль зарезервирован", entity_type="reservation", entity_id=str(saved["id"]), vehicle_id=vehicle_id)
        saved["status_ru"] = RESERVATION_LABELS["ACTIVE"]
        return {"ok": True, "item": saved}

    async def update_reservation(self, organization_id: str, reservation_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "edit") or can(role, "clients")):
            return require(role, "edit")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "reservations", reservation_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Резерв не найден"}
        status = _str(body.get("status") or item.get("status")).upper()
        if status not in RESERVATION_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус резерва"}
        item["status"] = status
        if "expires_at" in body:
            item["expires_at"] = body["expires_at"]
        item["updated_at"] = self._now()
        await self._persist_update("reservation", reservation_id, {"status": status, "expires_at": item.get("expires_at"), "updated_at": item["updated_at"]})
        action = "reservation_cancelled" if status == "CANCELLED" else "reservation_updated"
        await self._audit(organization_id=org, action=action, entity_type="reservation", entity_id=reservation_id, role=role, actor_id=actor_id, new_value={"status": status}, summary=action)
        return {"ok": True, "item": item}

    async def list_reservations(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._expire_reservations(org)
        items = list(self._bag(org)["reservations"])
        vid = (query or {}).get("vehicle_id") or ""
        if vid:
            items = [r for r in items if str(r.get("vehicle_id")) == vid]
        return {"ok": True, "items": items, "total": len(items)}

    async def create_sale(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "create") or can(role, "clients") or can(role, "finance_write")):
            return require(role, "create")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle_id = _str(body.get("vehicle_id"))
        client_id = _str(body.get("client_id"))
        deal_id = _str(body.get("deal_id")) or None
        vehicle = self._find(org, "vehicles", vehicle_id) if vehicle_id else None
        if not vehicle or not client_id:
            return {"ok": False, "error": "validation", "message_ru": "Продажа требует клиента и автомобиль"}
        if self._completed_sale(org, vehicle_id) or str(vehicle.get("status") or "") == "SOLD":
            return {"ok": False, "error": "conflict", "message_ru": "Автомобиль уже продан"}
        price = body.get("price") if body.get("price") not in (None, "") else body.get("sale_price")
        if price in (None, ""):
            return {"ok": False, "error": "validation", "message_ru": "Укажите цену продажи", "field": "price"}
        status = _str(body.get("status") or "OPEN").upper()
        if status not in SALE_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус продажи"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "vehicle_id": vehicle_id,
            "client_id": client_id,
            "deal_id": deal_id,
            "price": float(price),
            "currency": _str(body.get("currency") or "USD").upper() or "USD",
            "status": status,
            "completed_at": self._now() if status == "COMPLETED" else None,
            "notes": body.get("notes"),
            "is_demo": bool(body.get("is_demo")),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
        }
        saved = await self._persist("sale", item)
        self._bag(org)["sales"].insert(0, saved)
        if deal_id:
            deal = self._find(org, "deals", deal_id)
            if deal:
                deal["sale_price"] = float(price)
                deal["currency"] = item["currency"]
                if status == "COMPLETED":
                    deal["stage"] = "COMPLETED"
                deal["updated_at"] = self._now()
                await self._persist_update("deal", deal_id, {"sale_price": deal["sale_price"], "stage": deal.get("stage"), "updated_at": deal["updated_at"]})
        await self._apply_sale_status(org, saved, role, actor_id)
        await self._audit(organization_id=org, action="sale_created", entity_type="sale", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"vehicle_id": vehicle_id, "price": float(price)}, summary="sale_created")
        saved["status_ru"] = SALE_LABELS.get(status, status)
        return {"ok": True, "item": saved}

    async def _apply_sale_status(self, org: str, sale: dict[str, Any], role: str | None, actor_id: str | None) -> None:
        if str(sale.get("status") or "").upper() != "COMPLETED":
            return
        vid = str(sale.get("vehicle_id") or "")
        vehicle = self._find(org, "vehicles", vid)
        if vehicle:
            vehicle["status"] = "SOLD"
            vehicle["client_id"] = sale.get("client_id")
            vehicle["sale_price_actual"] = sale.get("price")
            vehicle["sale_currency"] = sale.get("currency")
            vehicle["sale_date"] = str(self._now())[:10]
            vehicle["updated_at"] = self._now()
            await self._persist_update("vehicle", vid, {"status": "SOLD", "client_id": vehicle["client_id"], "sale_price_actual": vehicle["sale_price_actual"], "sale_date": vehicle["sale_date"], "updated_at": vehicle["updated_at"]})
            await self._audit(organization_id=org, action="vehicle_sold", entity_type="vehicle", entity_id=vid, role=role, actor_id=actor_id, new_value={"sale_id": sale.get("id")}, summary="vehicle_sold")
        if sale.get("deal_id"):
            deal = self._find(org, "deals", str(sale["deal_id"]))
            if deal:
                deal["stage"] = "COMPLETED"
                deal["updated_at"] = self._now()
                await self._persist_update("deal", str(deal["id"]), {"stage": "COMPLETED", "updated_at": deal["updated_at"]})
            await self._audit(organization_id=org, action="deal_completed", entity_type="deal", entity_id=str(sale["deal_id"]), role=role, actor_id=actor_id, summary="deal_completed")
        res = self._active_reservation(org, vid)
        if res:
            res["status"] = "CONVERTED"
            res["updated_at"] = self._now()

    async def update_sale(self, organization_id: str, sale_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "edit") or can(role, "finance_write")):
            return require(role, "edit")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "sales", sale_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Продажа не найдена"}
        if str(item.get("status") or "").upper() == "COMPLETED" and body.get("delete"):
            return {"ok": False, "error": "conflict", "message_ru": "Завершённую продажу нельзя удалить. Используйте отмену."}
        old_price = item.get("price")
        if "price" in body or "sale_price" in body:
            item["price"] = float(body.get("price") if body.get("price") not in (None, "") else body.get("sale_price"))
        if "status" in body:
            status = _str(body.get("status")).upper()
            if status not in SALE_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус продажи"}
            item["status"] = status
            if status == "COMPLETED":
                item["completed_at"] = self._now()
                await self._apply_sale_status(org, item, role, actor_id)
        item["updated_at"] = self._now()
        await self._persist_update("sale", sale_id, {k: item.get(k) for k in ("price", "status", "completed_at", "updated_at")})
        action = "sale_price_changed" if item.get("price") != old_price else "sale_updated"
        await self._audit(organization_id=org, action=action, entity_type="sale", entity_id=sale_id, role=role, actor_id=actor_id, old_value={"price": old_price}, new_value={"price": item.get("price"), "status": item.get("status")}, summary=action)
        return {"ok": True, "item": item}

    async def list_sales(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["sales"])
        if not can(role, "finance") and not can(role, "clients"):
            return {"ok": False, "error": "forbidden", "message_ru": "Продажи доступны сотрудникам компании"}
        return {"ok": True, "items": items, "total": len(items)}

    async def create_receipt(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "finance_write") or can(role, "clients") or can(role, "create")):
            return require(role, "finance_write")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        kind = _str(body.get("kind") or "PARTIAL").upper()
        if kind not in RECEIPT_KIND_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип поступления", "field": "kind"}
        status = _str(body.get("status") or "pending").lower()
        if status not in RECEIPT_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус поступления"}
        if status == "confirmed" and not can(role, "finance_write"):
            return {"ok": False, "error": "forbidden", "message_ru": "Подтверждение платежа доступно бухгалтеру и директору"}
        amount = body.get("amount")
        try:
            amount_f = float(amount)
        except (TypeError, ValueError):
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму", "field": "amount"}
        currency = _str(body.get("currency") or "USD").upper() or "USD"
        rate = body.get("exchange_rate")
        try:
            rate_f = float(rate) if rate not in (None, "") else (1.0 if currency in {"USD", "UAH"} else None)
        except (TypeError, ValueError):
            rate_f = None
        base = round(amount_f * rate_f, 2) if rate_f is not None else None
        deal_id = _str(body.get("deal_id")) or None
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "deal_id": deal_id,
            "sale_id": _str(body.get("sale_id")) or None,
            "vehicle_id": _str(body.get("vehicle_id")) or None,
            "client_id": _str(body.get("client_id")) or None,
            "kind": kind,
            "amount": amount_f,
            "currency": currency,
            "exchange_rate": rate_f,
            "amount_base_currency": base,
            "status": status,
            "reference": _str(body.get("reference")) or None,
            "confirmed_at": self._now() if status == "confirmed" else None,
            "due_at": body.get("due_at"),
            "notes": body.get("notes"),
            "is_demo": bool(body.get("is_demo")),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
        }
        if deal_id:
            deal = self._find(org, "deals", deal_id)
            if deal:
                item["vehicle_id"] = item["vehicle_id"] or deal.get("vehicle_id")
                item["client_id"] = item["client_id"] or deal.get("client_id")
        saved = await self._persist("receipt", item)
        self._bag(org)["receipts"].insert(0, saved)
        action = "payment_confirmed" if status == "confirmed" else "payment_created"
        if kind == "REFUND":
            action = "refund"
        await self._audit(organization_id=org, action=action, entity_type="receipt", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={"amount": amount_f, "kind": kind, "status": status}, summary=action)
        if status == "confirmed":
            self._crm_notify(org, ntype="payment_confirmed", title="Платёж подтверждён", entity_type="receipt", entity_id=str(saved["id"]), vehicle_id=item.get("vehicle_id"))
        saved["kind_ru"] = RECEIPT_KIND_LABELS.get(kind, kind)
        return {"ok": True, "item": saved}

    async def update_receipt(self, organization_id: str, receipt_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not can(role, "finance_write"):
            return require(role, "finance_write")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "receipts", receipt_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Поступление не найдено"}
        if body.get("delete") or body.get("hard_delete"):
            return {"ok": False, "error": "conflict", "message_ru": "Финансовую запись нельзя удалить. Используйте void / cancel / refund."}
        old_status = str(item.get("status") or "")
        if old_status in CLOSED_FINANCIAL and "amount" in body and not body.get("void") and _str(body.get("status")).lower() not in {"void", "refunded", "cancelled"}:
            return {"ok": False, "error": "conflict", "message_ru": "Подтверждённый платёж нельзя править. Аннулируйте или оформите возврат."}
        action = "payment_changed"
        if body.get("void") or _str(body.get("status")).lower() == "void":
            item["status"] = "void"
            action = "payment_changed"
        elif _str(body.get("status")).lower() == "refunded" or body.get("refund"):
            item["status"] = "refunded"
            action = "refund"
        elif "status" in body:
            status = _str(body.get("status")).lower()
            if status not in RECEIPT_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус поступления"}
            if status == "confirmed":
                item["confirmed_at"] = self._now()
                action = "payment_confirmed"
            item["status"] = status
        elif old_status not in CLOSED_FINANCIAL and "amount" in body:
            item["amount"] = float(body["amount"])
        item["updated_at"] = self._now()
        await self._persist_update("receipt", receipt_id, {k: item.get(k) for k in ("status", "amount", "confirmed_at", "updated_at")})
        await self._audit(organization_id=org, action=action, entity_type="receipt", entity_id=receipt_id, role=role, actor_id=actor_id, old_value={"status": old_status}, new_value={"status": item.get("status"), "amount": item.get("amount")}, summary=action)
        return {"ok": True, "item": item}

    async def list_receipts(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        if not (can(role, "finance") or can(role, "clients")):
            return require(role, "finance")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["receipts"])
        q = query or {}
        if q.get("deal_id"):
            items = [r for r in items if str(r.get("deal_id") or "") == q["deal_id"]]
        if q.get("vehicle_id"):
            items = [r for r in items if str(r.get("vehicle_id") or "") == q["vehicle_id"]]
        return {"ok": True, "items": items, "total": len(items)}

    async def get_document_access(self, organization_id: str, document_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "documents", document_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        dtype = str(item.get("document_type") or "")
        identity = dtype in IDENTITY_DOC_TYPES or str(item.get("owner_type") or "") == "client" or dtype in {"passport", "id_card", "tax_id_copy"}
        rid = normalize_role(role)
        if identity:
            accountant_ok = rid == "auto_accountant"
            assigned_ok = rid == "auto_manager" and actor_id and (
                str(item.get("vehicle_id") or "") in {str(v.get("id")) for v in self._bag(org)["vehicles"] if str(v.get("assigned_manager_id") or "") == str(actor_id)}
                or str(item.get("client_id") or "") in {str(c.get("id")) for c in self._bag(org)["clients"] if str(c.get("assigned_manager_id") or "") == str(actor_id)}
            )
            if not (can(role, "pii") or accountant_ok or assigned_ok):
                return {"ok": False, "error": "forbidden", "message_ru": "Документы личности и договоры доступны директору, администратору, бухгалтеру (учёт) и менеджеру назначенного клиента"}
            await self._audit(organization_id=org, action="client_document_accessed", entity_type="document", entity_id=document_id, role=role, actor_id=actor_id, new_value={"document_type": dtype, "client_id": item.get("client_id")}, summary="client_document_accessed")
        return {"ok": True, "item": item}

    async def search_auto(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        q = ((query or {}).get("q") or (query or {}).get("search") or "").strip().upper()
        if not q:
            return {"ok": True, "items": [], "total": 0, "message_ru": "Введите VIN, клиента, перевозку, контейнер или BOL."}
        hits: list[dict[str, Any]] = []

        def add(kind: str, item_id: Any, title: str, extra: str = "") -> None:
            hay = f"{title} {extra}".upper()
            if q in hay:
                hits.append({"kind": kind, "id": str(item_id), "title": title, "extra": extra})

        for v in self._bag(org)["vehicles"]:
            add("vehicle", v.get("id"), self._vehicle_title(v), str(v.get("vin") or ""))
        for c in self._bag(org)["clients"]:
            pub = self._redact_client(c, role)
            phone = "" if pub.get("pii_restricted") and not can(role, "clients") else str(c.get("phone") or "")
            add("client", c.get("id"), str(c.get("name") or ""), phone)
        for d in self._bag(org)["deals"]:
            veh = self._find(org, "vehicles", str(d.get("vehicle_id") or "")) if d.get("vehicle_id") else None
            cli = self._find(org, "clients", str(d.get("client_id") or "")) if d.get("client_id") else None
            extra = " ".join(x for x in (str((veh or {}).get("vin") or ""), str((cli or {}).get("name") or ""), str(d.get("stage") or "")) if x)
            add("deal", d.get("id"), str(d.get("id")), extra)
        for r in self._bag(org)["receipts"]:
            add("payment", r.get("id"), str(r.get("reference") or r.get("id")), str(r.get("kind") or ""))
        for ctr in self._bag(org).get("containers") or []:
            add("container", ctr.get("id"), str(ctr.get("container_number") or ""), "")
        for ship in self._bag(org).get("shipments") or []:
            veh = self._find(org, "vehicles", str(ship.get("vehicle_id") or "")) if ship.get("vehicle_id") else None
            cli = self._find(org, "clients", str((veh or {}).get("client_id") or ship.get("client_id") or "")) if ((veh or {}).get("client_id") or ship.get("client_id")) else None
            extra = " ".join(
                x
                for x in (
                    str(ship.get("shipment_number") or ""),
                    str((veh or {}).get("vin") or ""),
                    str(ship.get("booking_number") or ""),
                    str(ship.get("bill_of_lading_number") or ""),
                    str(ship.get("tracking_reference") or ""),
                    str((cli or {}).get("name") or ""),
                )
                if x
            )
            add("shipment", ship.get("id"), str(ship.get("shipment_number") or ship.get("id")), extra)
            bol = str(ship.get("bill_of_lading_number") or "").strip()
            if bol:
                add("bol", ship.get("id"), bol, str(ship.get("shipment_number") or ""))
        for doc in self._bag(org)["documents"]:
            if doc.get("archived_at"):
                continue
            add("document", doc.get("id"), str(doc.get("file_name") or doc.get("title") or ""), str(doc.get("document_type") or doc.get("document_number") or ""))
        for case in self._bag(org).get("customs_cases") or []:
            veh = self._find(org, "vehicles", str(case.get("vehicle_id") or "")) if case.get("vehicle_id") else None
            broker = self._find(org, "brokers", str(case.get("broker_id") or "")) if case.get("broker_id") else None
            client = self._find(org, "clients", str((veh or {}).get("client_id") or "")) if (veh or {}).get("client_id") else None
            extra = " ".join(
                x
                for x in (
                    str((veh or {}).get("vin") or ""),
                    str(case.get("declaration_number") or ""),
                    str(case.get("registration_number") or ""),
                    str(case.get("plate_expected") or ""),
                    str((veh or {}).get("plate") or (veh or {}).get("license_plate") or ""),
                    str((broker or {}).get("company_name") or ""),
                    str((client or {}).get("name") or ""),
                    self._vehicle_title(veh) if veh else "",
                )
                if x
            )
            add("customs", case.get("id"), str(case.get("declaration_number") or case.get("id")), extra)
            if case.get("declaration_number"):
                add("declaration", case.get("id"), str(case.get("declaration_number")), str((veh or {}).get("vin") or ""))
        return {"ok": True, "items": hits[:50], "total": len(hits)}

    def _manager_metrics(self, org: str, manager_id: str | None = None) -> list[dict[str, Any]]:
        deals = list(self._bag(org)["deals"])
        managers: set[str] = {str(d.get("assigned_manager_id") or "") for d in deals if d.get("assigned_manager_id")}
        if manager_id:
            managers = {manager_id}
        out: list[dict[str, Any]] = []
        for mid in sorted(m for m in managers if m):
            mine = [d for d in deals if str(d.get("assigned_manager_id") or "") == mid]
            leads = sum(1 for d in mine if str(d.get("stage")) == "LEAD")
            contacts = sum(1 for d in mine if str(d.get("stage")) in {"CONTACT", "VEHICLE_SELECTED", "RESERVED", "DEPOSIT", "CONTRACT", "PARTIAL_PAYMENT", "FINAL_PAYMENT", "HANDOVER", "COMPLETED"})
            active = sum(1 for d in mine if str(d.get("stage")) not in {"COMPLETED", "CANCELLED", "LOST", "LEAD"})
            reservations = sum(1 for r in self._bag(org)["reservations"] if str(self._find(org, "deals", str(r.get("deal_id") or "")) or {}).get("assigned_manager_id") == mid or str(self._find(org, "clients", str(r.get("client_id") or "")) or {}).get("assigned_manager_id") == mid)
            completed = [d for d in mine if str(d.get("stage")) == "COMPLETED"]
            revenue = 0.0
            for d in completed:
                revenue += self._payment_rollup(org, d).get("paid") or 0
            tasks_open = sum(1 for t in self._bag(org)["tasks"] if str(t.get("assigned_manager_id") or "") == mid and t.get("status") in {"open", "in_progress"})
            out.append(
                {
                    "manager_id": mid,
                    "leads_assigned": leads,
                    "contacts_made": contacts,
                    "active_deals": active,
                    "reservations": reservations,
                    "completed_sales": len(completed),
                    "sales_revenue": round(revenue, 2),
                    "outstanding_tasks": tasks_open,
                    "score": None,
                    "ranking": None,
                    "note_ru": "Фактические счётчики. Балльной оценки сотрудников нет.",
                }
            )
        return out

    async def reports_desk(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "reports")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        q = query or {}
        report = (q.get("report") or q.get("type") or "sales").strip()
        dash = await self.dashboard(organization_id, role)
        vehicles = list(self._bag(org)["vehicles"])
        if q.get("manager"):
            vehicles = [v for v in vehicles if str(v.get("assigned_manager_id") or "") == q["manager"]]
        if q.get("vin"):
            vehicles = [v for v in vehicles if q["vin"].upper() in str(v.get("vin") or "").upper()]
        if q.get("status"):
            vehicles = [v for v in vehicles if str(v.get("status")) == q["status"].upper()]
        if q.get("vehicle") or q.get("vehicle_id"):
            vid = q.get("vehicle") or q.get("vehicle_id") or ""
            vehicles = [v for v in vehicles if str(v.get("id")) == vid]
        finance_ok = can(role, "finance")
        payload: dict[str, Any] = {"ok": True, "report": report, "filters": q, "from_records": True, "types": REPORT_TYPES, "scoring": False}
        if report == "sales":
            sales = [s for s in self._bag(org)["sales"] if str(s.get("status") or "").upper() != "CANCELLED"]
            payload["items"] = sales if finance_ok else [{"restricted": True}]
            payload["total"] = len(sales)
        elif report == "vehicle_profit":
            rows = []
            if finance_ok:
                for v in vehicles:
                    sale = self._completed_sale(org, str(v.get("id")))
                    revenue = _num((sale or {}).get("price")) or _num(v.get("sale_price_actual"))
                    snap = profit_snapshot(cost=self._vehicle_invested(org, str(v.get("id"))), revenue=revenue)
                    rows.append({"vehicle_id": v.get("id"), "title": self._vehicle_title(v), "vin": v.get("vin"), **snap})
            payload["items"] = rows
        elif report == "expenses":
            payload["items"] = [e for e in self._bag(org)["expenses"] if str(e.get("payment_status")) != "cancelled"] if finance_ok else []
        elif report == "receipts":
            payload["items"] = list(self._bag(org)["receipts"]) if finance_ok else []
        elif report == "client_debt":
            rows = []
            for d in self._bag(org)["deals"]:
                roll = self._payment_rollup(org, d)
                if roll.get("outstanding"):
                    rows.append({"deal_id": d.get("id"), "client_id": d.get("client_id"), "outstanding": roll["outstanding"], "currency": roll["currency"]})
            payload["items"] = rows if finance_ok else []
        elif report == "managers":
            payload["items"] = self._manager_metrics(org, q.get("manager"))
            payload["employee_scoring"] = False
        elif report == "funnel":
            counts = {i: 0 for i, _ in DEAL_STAGES}
            for d in self._bag(org)["deals"]:
                st = str(d.get("stage") or "")
                if st in counts:
                    counts[st] += 1
            payload["items"] = [{"stage": k, "label_ru": DEAL_STAGE_LABELS.get(k, k), "count": v} for k, v in counts.items()]
        elif report == "in_stock":
            payload["items"] = [self._public_vehicle(org, v) for v in vehicles if str(v.get("status") or "") in IN_STOCK_STATUSES]
        elif report == "in_transit":
            wanted = KPI_STATUS_GROUPS.get("in_transit", IN_TRANSIT_STATUSES)
            payload["items"] = [self._public_vehicle(org, v) for v in vehicles if str(v.get("status") or "") in wanted]
        else:
            payload["error"] = "unknown_report"
            payload["ok"] = False
            payload["message_ru"] = "Неизвестный тип отчёта"
            return payload
        payload["dashboard"] = dash if dash.get("ok") else {}
        payload["note_ru"] = "Отчёт по фактическим записям. Пустые цифры — нет данных, не «ноль рынка»."
        return payload

    async def seed_demo_crm(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not body.get("confirm_demo"):
            return {"ok": False, "error": "validation", "message_ru": "Для демо-сценария передайте confirm_demo=true. Демо никогда не смешивается с продакшен-записями без явного флага."}
        if not (can(role, "create") or can(role, "clients")):
            return require(role, "create")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle = await self.create_vehicle(
            org,
            {
                "vin": "WBAFR9C50DD777777",
                "allow_nonstandard_vin": True,
                "manufacturer": "BMW",
                "model": "X5",
                "year": 2018,
                "status": "READY_FOR_SALE",
                "location_current": "Склад (demo)",
                "auction_url": "https://demo.invalid/lot/crm-x5",
                "sale_price_expected": 28000,
            },
            role if can(role, "vin_override") else "auto_director",
            actor_id,
        )
        if not vehicle.get("ok"):
            return vehicle
        vid = str(vehicle["item"]["id"])
        vrow = self._find(org, "vehicles", vid)
        if vrow:
            vrow["is_demo"] = True
            vrow["notes"] = "DEMO — AUTO 1.3 CRM scenario."
        client = await self.create_client(
            org,
            {"name": "DEMO CLIENT", "phone": "+38000000001", "email": "demo.client@invalid", "assigned_manager_id": "demo-manager", "status": "lead", "source": "demo"},
            role if can(role, "clients") else "auto_director",
            actor_id,
        )
        if not client.get("ok"):
            return client
        cid = str(client["item"]["id"])
        crow = self._find(org, "clients", cid)
        if crow:
            crow["is_demo"] = True
        deal = await self.create_deal(org, {"client_id": cid, "vehicle_id": vid, "stage": "LEAD", "assigned_manager_id": "demo-manager", "sale_price": 28000, "currency": "USD", "is_demo": True}, role, actor_id)
        did = str((deal.get("item") or {}).get("id") or "")
        await self.update_deal(org, did, {"stage": "CONTACT"}, role, actor_id)
        await self.update_deal(org, did, {"stage": "VEHICLE_SELECTED"}, role, actor_id)
        await self.create_reservation(org, {"vehicle_id": vid, "client_id": cid, "deal_id": did, "expires_at": "2026-12-31", "is_demo": True}, role, actor_id)
        await self.create_sale(org, {"vehicle_id": vid, "client_id": cid, "deal_id": did, "price": 28000, "currency": "USD", "status": "OPEN", "is_demo": True}, role, actor_id)
        acc = "auto_accountant"
        await self.create_receipt(org, {"deal_id": did, "vehicle_id": vid, "client_id": cid, "kind": "DEPOSIT", "amount": 5000, "currency": "USD", "status": "confirmed", "reference": "DEMO-DEP-1"}, acc, actor_id)
        await self.create_receipt(org, {"deal_id": did, "vehicle_id": vid, "client_id": cid, "kind": "PARTIAL", "amount": 10000, "currency": "USD", "status": "confirmed", "reference": "DEMO-PAR-1"}, acc, actor_id)
        await self.create_receipt(org, {"deal_id": did, "vehicle_id": vid, "client_id": cid, "kind": "FINAL", "amount": 13000, "currency": "USD", "status": "confirmed", "reference": "DEMO-FIN-1"}, acc, actor_id)
        await self.update_deal(org, did, {"stage": "HANDOVER"}, role, actor_id)
        sales = [s for s in self._bag(org)["sales"] if str(s.get("deal_id")) == did]
        if sales:
            await self.update_sale(org, str(sales[0]["id"]), {"status": "COMPLETED"}, role, actor_id)
        await self.create_document(org, {"owner_type": "client", "client_id": cid, "deal_id": did, "vehicle_id": vid, "file_name": "demo-contract.pdf", "document_type": "sale_agreement"}, role, actor_id)
        await self.create_task(org, {"title": "Выдать авто клиенту (demo)", "vehicle_id": vid, "client_id": cid, "deal_id": did, "priority": "high"}, role, actor_id)
        await self.create_expense(org, {"vehicle_id": vid, "category": "PURCHASE", "amount": 18000, "currency": "USD", "payment_status": "paid", "description": "DEMO purchase"}, acc, actor_id)
        refreshed = await self.get_deal(org, did, role)
        return {
            "ok": True,
            "demo": True,
            "label_ru": "Демо-сценарий AUTO 1.3. Не продакшен.",
            "vehicle": vehicle.get("item"),
            "client": client.get("item"),
            "deal": refreshed.get("item") if refreshed.get("ok") else deal.get("item"),
        }

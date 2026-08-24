"""AUTO 1.6 document OS mixin — packages, templates, generation, dossiers, validation.

Extends existing Auto documents/files. No new bot, no fake e-sign, no mandatory OCR.
"""

from __future__ import annotations

import io
import logging
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any

from services.auto_ops.analytics_catalog import csv_bytes
from services.auto_ops.catalog import DOCUMENT_IDS
from services.auto_ops.crm_catalog import IDENTITY_DOC_TYPES
from services.auto_ops.documents_catalog import (
    CHECKLIST_TEMPLATE_DEFS,
    DOSSIER_GROUPS,
    EXPORT_COLUMNS,
    EXTRA_DOCUMENT_TYPES,
    FINANCE_DOC_TYPES,
    FINANCE_VERIFY_IDS,
    GENERATION_BY_ID,
    GENERATION_TEMPLATES,
    LEGAL_DISCLAIMER_RU,
    REGISTRATION_PACKAGE_ITEMS,
    SALE_PACKAGE_ITEMS,
    SIGNATURE_IDS,
    TYPE_TO_DOSSIER,
    WORKFLOW_IDS,
    document_label,
    documents_catalogs,
    extract_vin_hint,
    render_placeholders,
)
from services.auto_ops.files import read_bytes, storage_root, validate_upload, write_bytes
from services.auto_ops.rbac import can, normalize_role, require

logger = logging.getLogger(__name__)

DOCUMENTS_BAG_KEYS = ("document_templates",)

_EXTRA_DOC_IDS = frozenset(i for i, _ in EXTRA_DOCUMENT_TYPES)
ALL_DOC_IDS = DOCUMENT_IDS | _EXTRA_DOC_IDS

_AUDIT_DOC_ACTIONS = frozenset(
    {
        "document_uploaded",
        "document_generated",
        "document_approved",
        "document_status",
        "document_renamed",
        "document_type_changed",
        "document_replaced",
        "document_deleted",
        "document_linked",
        "document_unlinked",
        "document_restored",
        "telegram_doc",
        "telegram_docs",
    }
)


class AutoOpsDocumentsMixin:
    """Sale/registration packages, checklist templates, DRAFT generation, dossiers."""

    def _all_document_ids(self) -> frozenset[str]:
        return ALL_DOC_IDS

    def _ensure_document_templates(self, org: str) -> None:
        bag = self._bag(org)
        items = bag["document_templates"]
        if any(not t.get("is_company") for t in items):
            return
        now = self._now()
        seeded: list[dict[str, Any]] = []
        for spec in CHECKLIST_TEMPLATE_DEFS:
            for dtype, name, required, sort_order in spec["items"]:
                seeded.append(
                    {
                        "id": str(uuid.uuid4()),
                        "organization_id": org,
                        "tenant_id": org,
                        "name": name,
                        "stage": spec["stage"],
                        "stage_name": spec["name"],
                        "document_type": dtype,
                        "required": bool(required),
                        "sort_order": int(sort_order),
                        "active": True,
                        "configurable": bool(spec.get("configurable")),
                        "note_ru": spec.get("note_ru"),
                        "is_default": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
        bag["document_templates"] = seeded + items

    def _active_docs(self, org: str, vehicle_id: str | None = None) -> list[dict[str, Any]]:
        rows = [d for d in self._bag(org)["documents"] if not d.get("archived_at")]
        if vehicle_id:
            rows = [d for d in rows if str(d.get("vehicle_id") or "") == str(vehicle_id)]
        return rows

    def _document_visible(self, org: str, doc: dict[str, Any], role: str | None, actor_id: str | None) -> bool:
        rid = normalize_role(role)
        if can(rid, "admin") or can(rid, "pii"):
            return True
        dtype = str(doc.get("document_type") or "")
        identity = dtype in IDENTITY_DOC_TYPES or str(doc.get("owner_type") or "") == "client" or dtype in {"passport", "id_card", "tax_id_copy"}
        if rid == "auto_accountant":
            return dtype in FINANCE_DOC_TYPES or identity or dtype in {"sale_agreement", "contract", "invoice", "transfer_act"}
        if rid == "auto_manager" and actor_id:
            vids = {str(v.get("id")) for v in self._bag(org)["vehicles"] if str(v.get("assigned_manager_id") or "") == str(actor_id)}
            cids = {str(c.get("id")) for c in self._bag(org)["clients"] if str(c.get("assigned_manager_id") or "") == str(actor_id)}
            if str(doc.get("vehicle_id") or "") in vids or str(doc.get("client_id") or "") in cids:
                return True
            return False
        if identity and not can(rid, "pii"):
            return False
        return True

    def _filter_documents(self, org: str, items: list[dict[str, Any]], role: str | None, actor_id: str | None) -> list[dict[str, Any]]:
        return [d for d in items if self._document_visible(org, d, role, actor_id)]

    def _public_document(self, org: str, doc: dict[str, Any], role: str | None) -> dict[str, Any]:
        vehicle = self._find(org, "vehicles", str(doc.get("vehicle_id") or "")) if doc.get("vehicle_id") else None
        client = self._find(org, "clients", str(doc.get("client_id") or (vehicle or {}).get("client_id") or "")) if (doc.get("client_id") or (vehicle or {}).get("client_id")) else None
        out = dict(doc)
        out["type_ru"] = document_label(str(doc.get("document_type") or ""))
        out["category"] = doc.get("category") or TYPE_TO_DOSSIER.get(str(doc.get("document_type") or ""), "other")
        out["vehicle_title"] = self._vehicle_title(vehicle) if vehicle else ""
        out["vin"] = (vehicle or {}).get("vin") or doc.get("extracted_vin") or ""
        out["client_name"] = (client or {}).get("name") or ""
        out["workflow_status"] = doc.get("workflow_status") or ("DRAFT" if doc.get("generated") else "")
        out["signature_status"] = doc.get("signature_status") or "NOT_REQUIRED"
        out["finance_verify"] = doc.get("finance_verify") or "UNVERIFIED"
        if not can(role, "admin"):
            out.pop("storage_path", None)
            out.pop("checksum", None)
            file_id = out.get("file_id")
            if file_id:
                meta = self._find(org, "files", str(file_id))
                if meta:
                    out["has_file"] = True
                    out["file_size"] = meta.get("size_bytes")
        return out

    def _item_present(self, org: str, vehicle: dict[str, Any] | None, spec: dict[str, Any], docs: list[dict[str, Any]]) -> bool:
        kind = spec.get("kind")
        if kind == "entity":
            return bool(vehicle)
        if kind == "vin":
            return bool(str((vehicle or {}).get("vin") or "").strip())
        client = self._find(org, "clients", str((vehicle or {}).get("client_id") or "")) if vehicle and vehicle.get("client_id") else None
        if kind == "client":
            return bool(client)
        if kind == "client_field":
            field = str(spec.get("field") or "")
            if client and str(client.get(field) or "").strip():
                return True
            types = set(spec.get("document_types") or [])
            return any(str(d.get("document_type") or "") in types for d in docs)
        if kind in {"document", "payment"}:
            types = set(spec.get("document_types") or [])
            if any(str(d.get("document_type") or "") in types for d in docs):
                return True
            if kind == "payment" and vehicle:
                vid = str(vehicle.get("id"))
                receipts = [r for r in self._bag(org)["receipts"] if str(r.get("vehicle_id") or "") == vid and str(r.get("status") or "") in {"confirmed", "posted", "received"}]
                if receipts:
                    return True
            return False
        return False

    def _eval_package(self, org: str, vehicle: dict[str, Any] | None, items: list[dict[str, Any]]) -> dict[str, Any]:
        docs = self._active_docs(org, str(vehicle.get("id")) if vehicle else None)
        checklist = []
        missing: list[str] = []
        for spec in sorted(items, key=lambda s: int(s.get("sort_order") or 0)):
            present = self._item_present(org, vehicle, spec, docs)
            row = {**spec, "present": present, "label_ru": spec.get("name")}
            checklist.append(row)
            if spec.get("required") and not present:
                missing.append(str(spec.get("name") or spec.get("id")))
        ready = not missing and bool(vehicle)
        return {
            "ok": True,
            "ready": ready,
            "status_ru": "ГОТОВО К ПРОДАЖЕ" if items is SALE_PACKAGE_ITEMS and ready else ("ГОТОВО" if ready else "НЕ ГОТОВО"),
            "missing": missing,
            "items": checklist,
            "present_count": sum(1 for i in checklist if i.get("present")),
            "required_count": sum(1 for i in checklist if i.get("required")),
            "configurable": items is REGISTRATION_PACKAGE_ITEMS,
            "note_ru": (
                "Шаблон регистрации настраивается администратором. Это операционные заготовки, не юридический перечень."
                if items is REGISTRATION_PACKAGE_ITEMS
                else None
            ),
        }

    def document_counters_for_vehicle(self, org: str, vehicle: dict[str, Any]) -> dict[str, Any]:
        docs = self._active_docs(org, str(vehicle.get("id")))
        sale = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS)
        return {
            "document_count": len(docs),
            "missing_count": len(sale.get("missing") or []),
            "sale_ready": bool(sale.get("ready")),
        }

    async def sale_package(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vid = str((query or {}).get("vehicle_id") or (query or {}).get("deal_id") or "")
        vehicle = self._find(org, "vehicles", vid)
        if not vehicle and (query or {}).get("deal_id"):
            deal = self._find(org, "deals", str(query.get("deal_id")))
            if deal and deal.get("vehicle_id"):
                vehicle = self._find(org, "vehicles", str(deal["vehicle_id"]))
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль для пакета продажи не найден"}
        pack = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS)
        pack["kind"] = "sale"
        pack["vehicle_id"] = vehicle.get("id")
        pack["vin"] = vehicle.get("vin")
        pack["title"] = self._vehicle_title(vehicle)
        return pack

    async def registration_package(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._ensure_document_templates(org)
        vehicle = self._find(org, "vehicles", str((query or {}).get("vehicle_id") or ""))
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль для пакета регистрации не найден"}
        tmpl = [t for t in self._bag(org)["document_templates"] if t.get("stage") == "registration" and t.get("active") is not False]
        items = []
        if tmpl:
            for t in sorted(tmpl, key=lambda r: int(r.get("sort_order") or 0)):
                types = [str(t.get("document_type") or "")]
                items.append(
                    {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "kind": "document" if types[0] in ALL_DOC_IDS else "client_field",
                        "document_types": types,
                        "field": "passport_ref" if "identity" in str(t.get("name") or "").lower() or types[0] in {"passport", "id_card"} else "tax_id",
                        "required": bool(t.get("required")),
                        "sort_order": t.get("sort_order"),
                        "placeholder": True,
                    }
                )
        else:
            items = list(REGISTRATION_PACKAGE_ITEMS)
        pack = self._eval_package(org, vehicle, items)
        pack["kind"] = "registration"
        pack["configurable"] = True
        pack["vehicle_id"] = vehicle.get("id")
        pack["status_ru"] = "ГОТОВО" if pack.get("ready") else "НЕ ГОТОВО"
        pack["note_ru"] = "Шаблон регистрации настраивается в Настройки → Документы. Юридические нормы не выдумываются."
        return pack

    async def list_document_templates(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._ensure_document_templates(org)
        items = [t for t in self._bag(org)["document_templates"] if not t.get("is_company")]
        stage = (query or {}).get("stage") or ""
        if stage:
            items = [t for t in items if str(t.get("stage")) == stage]
        items.sort(key=lambda t: (str(t.get("stage") or ""), int(t.get("sort_order") or 0)))
        return {
            "ok": True,
            "items": items,
            "stages": [{"id": s["stage"], "name": s["name"], "configurable": bool(s.get("configurable")), "note_ru": s.get("note_ru")} for s in CHECKLIST_TEMPLATE_DEFS],
            "configurable": True,
        }

    async def save_document_template(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "admin") or can(role, "edit")):
            return require(role, "admin")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._ensure_document_templates(org)
        name = str(body.get("name") or "").strip()
        stage = str(body.get("stage") or "").strip()
        if not name or not stage:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название и этап шаблона"}
        item_id = str(body.get("id") or "").strip()
        existing = self._find(org, "document_templates", item_id) if item_id else None
        payload = {
            "name": name,
            "stage": stage,
            "document_type": str(body.get("document_type") or "other"),
            "required": bool(body.get("required", True)),
            "sort_order": int(body.get("sort_order") or 0),
            "active": bool(body.get("active", True)),
            "configurable": True,
            "updated_at": self._now(),
        }
        if existing:
            old = {k: existing.get(k) for k in payload}
            existing.update(payload)
            await self._persist_update("document_template", item_id, payload)
            await self._audit(organization_id=org, action="document_template_updated", entity_type="document_template", entity_id=item_id, role=role, actor_id=actor_id, old_value=old, new_value=payload)
            return {"ok": True, "item": existing}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "created_at": self._now(),
            "is_default": False,
            **payload,
        }
        saved = await self._persist("document_template", item)
        self._bag(org)["document_templates"].append(saved)
        await self._audit(organization_id=org, action="document_template_created", entity_type="document_template", entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value=payload)
        return {"ok": True, "item": saved}

    async def delete_document_template(self, organization_id: str, template_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not can(role, "admin"):
            return require(role, "admin")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "document_templates", template_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Пункт шаблона не найден"}
        item["active"] = False
        item["updated_at"] = self._now()
        await self._persist_update("document_template", template_id, {"active": False, "updated_at": item["updated_at"]})
        await self._audit(organization_id=org, action="document_template_removed", entity_type="document_template", entity_id=template_id, role=role, actor_id=actor_id, old_value={"name": item.get("name")})
        return {"ok": True, "item": item, "soft": True}

    def _company_profile(self, org: str) -> dict[str, str]:
        for t in self._bag(org)["document_templates"]:
            if t.get("is_company"):
                return {"name": str(t.get("name") or ""), "details": str(t.get("note_ru") or t.get("details") or "")}
        return {"name": "", "details": ""}

    async def save_company_profile(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not can(role, "admin"):
            return require(role, "admin")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        self._ensure_document_templates(org)
        name = str(body.get("name") or body.get("company_name") or "").strip()
        details = str(body.get("details") or body.get("company_details") or "").strip()
        existing = next((t for t in self._bag(org)["document_templates"] if t.get("is_company")), None)
        payload = {
            "name": name,
            "stage": "company_profile",
            "document_type": "other",
            "required": False,
            "sort_order": 0,
            "active": True,
            "is_company": True,
            "note_ru": details,
            "details": details,
            "updated_at": self._now(),
        }
        if existing:
            existing.update(payload)
            await self._persist_update("document_template", str(existing["id"]), payload)
            return {"ok": True, "item": {"name": name, "details": details}}
        item = {"id": str(uuid.uuid4()), "organization_id": org, "tenant_id": org, "created_at": self._now(), **payload}
        saved = await self._persist("document_template", item)
        self._bag(org)["document_templates"].append(saved)
        return {"ok": True, "item": {"name": name, "details": details}}

    def _placeholder_values(self, org: str, vehicle: dict[str, Any] | None, client: dict[str, Any] | None, deal: dict[str, Any] | None) -> dict[str, str]:
        company = self._company_profile(org)
        return {
            "vehicle.vin": str((vehicle or {}).get("vin") or ""),
            "vehicle.make": str((vehicle or {}).get("manufacturer") or ""),
            "vehicle.model": str((vehicle or {}).get("model") or ""),
            "vehicle.year": str((vehicle or {}).get("year") or ""),
            "client.full_name": str((client or {}).get("name") or ""),
            "client.tax_number": str((client or {}).get("tax_id") or ""),
            "deal.sale_price": str((deal or {}).get("sale_price") or (deal or {}).get("price") or (vehicle or {}).get("sale_price_expected") or ""),
            "deal.date": str((deal or {}).get("created_at") or self._now())[:10],
            "company.name": company.get("name") or "",
            "company.details": company.get("details") or "",
        }

    async def generate_document(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        tmpl_id = str(body.get("template_id") or body.get("template") or "sale_agreement_draft")
        spec = GENERATION_BY_ID.get(tmpl_id)
        if not spec:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный шаблон документа"}
        vehicle = self._find(org, "vehicles", str(body.get("vehicle_id") or "")) if body.get("vehicle_id") else None
        deal = self._find(org, "deals", str(body.get("deal_id") or "")) if body.get("deal_id") else None
        if deal and not vehicle and deal.get("vehicle_id"):
            vehicle = self._find(org, "vehicles", str(deal["vehicle_id"]))
        client = None
        cid = body.get("client_id") or (vehicle or {}).get("client_id") or (deal or {}).get("client_id")
        if cid:
            client = self._find(org, "clients", str(cid))
        values = self._placeholder_values(org, vehicle, client, deal)
        text = render_placeholders(spec["body"], values)
        filename = f"{spec['id']}.txt"
        file_id = str(uuid.uuid4())
        write_bytes(org, file_id, text.encode("utf-8"))
        meta = {
            "id": file_id,
            "organization_id": org,
            "tenant_id": org,
            "file_name": filename,
            "mime_type": "text/plain",
            "storage_path": str(storage_root() / org / file_id),
            "size_bytes": len(text.encode("utf-8")),
            "uploaded_by": actor_id or normalize_role(role),
            "entity_type": "vehicle",
            "entity_id": (vehicle or {}).get("id"),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        saved_file = await self._persist("file", meta)
        self._bag(org)["files"].insert(0, saved_file)
        created = await self.create_document(
            org,
            {
                "document_type": spec["document_type"],
                "title": spec["name_ru"],
                "file_name": filename,
                "file_id": file_id,
                "owner_type": "vehicle" if vehicle else "deal",
                "vehicle_id": (vehicle or {}).get("id"),
                "client_id": (client or {}).get("id"),
                "deal_id": (deal or {}).get("id"),
                "generated": True,
                "template_id": tmpl_id,
                "workflow_status": "DRAFT",
                "signature_status": "NOT_REQUIRED",
                "legal_disclaimer": LEGAL_DISCLAIMER_RU,
                "source": str(body.get("source") or "WEB"),
                "notes": LEGAL_DISCLAIMER_RU,
            },
            role,
            actor_id,
        )
        if not created.get("ok"):
            return created
        item = created["item"]
        await self._audit(organization_id=org, action="document_generated", entity_type="document", entity_id=str(item["id"]), role=role, actor_id=actor_id, new_value={"template_id": tmpl_id, "draft": True}, summary="document_generated")
        return {
            "ok": True,
            "item": self._public_document(org, item, role),
            "draft": True,
            "legal_disclaimer_ru": LEGAL_DISCLAIMER_RU,
            "message_ru": "Документ создан как черновик. Это шаблон, не юридически гарантированный текст.",
        }

    async def documents_desk(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        listed = await self.list_documents(org, role, query or {}, actor_id)
        items = [self._public_document(org, d, role) for d in listed.get("items") or []]
        now = datetime.now(timezone.utc).date()
        soon = now + timedelta(days=14)
        missing = 0
        review = 0
        expiring = 0
        rejected = 0
        for v in self._bag(org)["vehicles"]:
            if str(v.get("status")) in {"CANCELLED", "INTEREST"}:
                continue
            pack = self._eval_package(org, v, SALE_PACKAGE_ITEMS)
            missing += len(pack.get("missing") or [])
        for d in items:
            if str(d.get("workflow_status") or "") == "REVIEW" or str(d.get("finance_verify") or "") == "UNVERIFIED" and d.get("document_type") in FINANCE_DOC_TYPES:
                review += 1
            if str(d.get("finance_verify") or d.get("signature_status") or "") == "REJECTED" or str(d.get("workflow_status") or "") == "REJECTED":
                rejected += 1
            until = str(d.get("valid_until") or "")[:10]
            if until:
                try:
                    day = datetime.fromisoformat(until).date()
                    if now <= day <= soon:
                        expiring += 1
                except ValueError:
                    pass
        return {
            "ok": True,
            "sprint": "AUTO_1.8.5",
            "kpis": {
                "total": len(items),
                "missing": missing,
                "review": review,
                "expiring": expiring,
                "rejected": rejected,
            },
            "items": items,
            "generation_templates": [{"id": t["id"], "name_ru": t["name_ru"], "draft": True} for t in GENERATION_TEMPLATES],
        }

    async def document_dossiers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vid = str((query or {}).get("vehicle_id") or "")
        vehicle = self._find(org, "vehicles", vid)
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль не найден"}
        docs = [self._public_document(org, d, role) for d in self._filter_documents(org, self._active_docs(org, vid), role, actor_id)]
        groups: dict[str, list[dict[str, Any]]] = {k: [] for k in DOSSIER_GROUPS}
        for d in docs:
            cat = str(d.get("category") or TYPE_TO_DOSSIER.get(str(d.get("document_type") or ""), "finance"))
            groups.setdefault(cat, []).append(d)
        expenses = [e for e in self._bag(org)["expenses"] if str(e.get("vehicle_id")) == vid]
        shipments = [s for s in self._bag(org).get("shipments", []) if str(s.get("vehicle_id") or "") == vid]
        return {
            "ok": True,
            "vehicle_id": vid,
            "vin": vehicle.get("vin"),
            "customs": {"label_ru": "Растаможка", "items": groups.get("customs") or [], "finance": [e for e in expenses if str(e.get("category") or "") in {"CUSTOMS", "DUTY", "EXCISE", "IMPORT_VAT", "BROKER"}]},
            "logistics": {"label_ru": "Логистика", "items": groups.get("logistics") or [], "shipments": [{"id": s.get("id"), "container": s.get("container_number"), "booking": s.get("booking_ref")} for s in shipments]},
            "payment": {"label_ru": "Платежи", "items": groups.get("payment") or []},
            "purchase": {"items": groups.get("purchase") or []},
            "sale": {"items": groups.get("sale") or []},
            "registration": {"items": groups.get("registration") or []},
            "client": {"items": groups.get("client") or []},
            "finance": {"items": groups.get("finance") or []},
        }

    async def document_timeline(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vid = str((query or {}).get("vehicle_id") or "")
        events = []
        for a in self._bag(org)["audit"]:
            action = str(a.get("action") or "")
            if vid and str(a.get("entity_id") or "") != vid and str((a.get("new_value") or {}).get("vehicle_id") or "") != vid:
                if action not in _AUDIT_DOC_ACTIONS:
                    continue
                doc = self._find(org, "documents", str(a.get("entity_id") or ""))
                if not doc or str(doc.get("vehicle_id") or "") != vid:
                    continue
            elif action not in _AUDIT_DOC_ACTIONS and str(a.get("entity_type") or "") != "document":
                continue
            events.append(
                {
                    "id": a.get("id"),
                    "at": a.get("created_at"),
                    "action": action,
                    "actor": a.get("actor_id") or a.get("actor_role"),
                    "source": (a.get("new_value") or {}).get("source") or ("TELEGRAM" if action.startswith("telegram_") else "WEB"),
                    "summary_ru": self._timeline_label(a),
                }
            )
        events.sort(key=lambda e: str(e.get("at") or ""), reverse=True)
        return {"ok": True, "items": events[:80]}

    def _timeline_label(self, audit: dict[str, Any]) -> str:
        action = str(audit.get("action") or "")
        actor = audit.get("actor_id") or audit.get("actor_role") or "сотрудник"
        labels = {
            "document_uploaded": f"Документ загружен · {actor}",
            "document_generated": f"Документ сгенерирован · {actor}",
            "document_approved": f"Документ утверждён · {actor}",
            "document_status": f"Статус документа изменён · {actor}",
            "telegram_doc": f"Документ загружен через Telegram · {actor}",
            "document_deleted": f"Документ удалён · {actor}",
            "document_linked": f"Документ привязан · {actor}",
        }
        return labels.get(action, f"{action} · {actor}")

    def validate_document_record(self, org: str, doc: dict[str, Any], file_meta: dict[str, Any] | None = None) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if not doc.get("file_id") and not doc.get("generated"):
            issues.append({"code": "missing_file", "message_ru": "Нет файла"})
        meta = file_meta or (self._find(org, "files", str(doc.get("file_id"))) if doc.get("file_id") else None)
        if meta and int(meta.get("size_bytes") or 0) == 0:
            issues.append({"code": "zero_byte", "message_ru": "Файл пустой"})
        if doc.get("file_name"):
            err = validate_upload(str(doc.get("file_name")), meta.get("mime_type") if meta else None)
            if err and str(doc.get("file_name") or "").endswith(".txt") is False:
                issues.append({"code": "unsupported_type", "message_ru": err.get("message_ru") or "Неподдерживаемый тип"})
        until = str(doc.get("valid_until") or "")[:10]
        if until:
            try:
                if datetime.fromisoformat(until).date() < datetime.now(timezone.utc).date():
                    issues.append({"code": "expired", "message_ru": "Срок документа истёк"})
            except ValueError:
                issues.append({"code": "missing_metadata", "message_ru": "Некорректная дата срока"})
        vid = str(doc.get("vehicle_id") or "")
        if vid and not self._find(org, "vehicles", vid):
            issues.append({"code": "wrong_vehicle", "message_ru": "Автомобиль не найден"})
        dtype = str(doc.get("document_type") or "")
        if dtype and vid:
            twins = [
                d
                for d in self._active_docs(org, vid)
                if str(d.get("document_type")) == dtype and str(d.get("id")) != str(doc.get("id")) and str(d.get("title") or "") == str(doc.get("title") or "")
            ]
            if twins:
                issues.append({"code": "duplicate", "message_ru": "Похожий документ уже есть"})
        if dtype in {"invoice", "customs_declaration", "certificate", "title", "registration"} and not doc.get("document_number"):
            issues.append({"code": "missing_metadata", "message_ru": "Нет номера документа"})
        extracted = str(doc.get("extracted_vin") or "").upper()
        vehicle = self._find(org, "vehicles", vid) if vid else None
        if extracted and vehicle and extracted != str(vehicle.get("vin") or "").upper():
            issues.append({"code": "vin_conflict", "message_ru": "Извлечённый VIN не совпадает с выбранным автомобилем"})
        return issues

    async def check_document_completeness(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vid = str(body.get("vehicle_id") or "")
        vehicle = self._find(org, "vehicles", vid) if vid else None
        sale = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS) if vehicle else {"missing": ["Автомобиль"]}
        registration = await self.registration_package(org, role, {"vehicle_id": vid}, actor_id) if vehicle else {"missing": ["Автомобиль"]}
        docs = [self._public_document(org, d, role) for d in self._active_docs(org, vid)] if vehicle else []
        issues = []
        for d in docs:
            issues.extend({"document_id": d.get("id"), **i} for i in self.validate_document_record(org, d))
        return {
            "ok": True,
            "sale": sale,
            "registration": registration,
            "issues": issues,
            "message_ru": (
                "Комплект готов."
                if not sale.get("missing") and not (registration.get("missing") if isinstance(registration, dict) else True)
                else f"Не хватает {len(sale.get('missing') or [])} позиций пакета продажи."
            ),
        }

    async def export_documents_csv(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "documents") or can(role, "reports")):
            return require(role, "documents")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        listed = await self.list_documents(org, role, query or {}, actor_id)
        rows = []
        for d in listed.get("items") or []:
            pub = self._public_document(org, d, role)
            rows.append(
                [
                    pub.get("vehicle_title"),
                    pub.get("vin"),
                    pub.get("client_name"),
                    pub.get("type_ru"),
                    pub.get("document_number"),
                    str(pub.get("issued_date") or pub.get("created_at") or "")[:10],
                    pub.get("valid_until"),
                    pub.get("workflow_status") or pub.get("finance_verify") or "",
                    pub.get("uploaded_by"),
                ]
            )
        raw = csv_bytes(EXPORT_COLUMNS, rows)
        return {"ok": True, "filename": "auto-documents.csv", "content_type": "text/csv; charset=utf-8", "content": raw, "format": "csv"}

    async def zip_vehicle_dossier(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vid = str((query or {}).get("vehicle_id") or "")
        vehicle = self._find(org, "vehicles", vid)
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль не найден"}
        vin = str(vehicle.get("vin") or "VEHICLE")
        docs = self._filter_documents(org, self._active_docs(org, vid), role, actor_id)
        buf = io.BytesIO()
        added = 0
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for group, spec in DOSSIER_GROUPS.items():
                zf.writestr(f"{vin}/{spec['label_ru'] if False else group.capitalize()}/", "")
            folder = {
                "purchase": "Purchase",
                "logistics": "Logistics",
                "customs": "Customs",
                "registration": "Registration",
                "sale": "Sale",
                "client": "Client",
                "finance": "Finance",
                "payment": "Finance",
            }
            for d in docs:
                file_id = str(d.get("file_id") or "")
                meta = self._find(org, "files", file_id) if file_id else None
                if not meta:
                    continue
                path = str(meta.get("storage_path") or "")
                raw = read_bytes(path) if path else None
                if raw is None:
                    continue
                cat = folder.get(str(d.get("category") or TYPE_TO_DOSSIER.get(str(d.get("document_type") or ""), "finance")), "Finance")
                name = str(d.get("file_name") or f"{d.get('id')}.bin")
                zf.writestr(f"{vin}/{cat}/{name}", raw)
                added += 1
        if not added:
            return {"ok": False, "error": "empty", "message_ru": "В досье нет файлов для архива"}
        return {
            "ok": True,
            "filename": f"{vin}-dossier.zip",
            "content_type": "application/zip",
            "content": buf.getvalue(),
            "files": added,
        }

    async def update_document_status(self, organization_id: str, document_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "documents")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "documents", document_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Документ не найден"}
        old = {k: item.get(k) for k in ("workflow_status", "signature_status", "finance_verify")}
        patch: dict[str, Any] = {"updated_at": self._now()}
        if "workflow_status" in body:
            status = str(body.get("workflow_status") or "").upper()
            if status not in WORKFLOW_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус документа"}
            if status == "APPROVED":
                dtype = str(item.get("document_type") or "")
                if dtype in FINANCE_DOC_TYPES and not (can(role, "finance") or can(role, "admin")):
                    return {"ok": False, "error": "forbidden", "message_ru": "Финансовые документы утверждает бухгалтер или директор"}
                if dtype in {"sale_agreement", "contract", "transfer_act"} and not (can(role, "pii") or can(role, "admin")):
                    return {"ok": False, "error": "forbidden", "message_ru": "Финальный пакет продажи утверждает директор"}
            patch["workflow_status"] = status
        if "signature_status" in body:
            sig = str(body.get("signature_status") or "").upper()
            if sig not in SIGNATURE_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус подписи"}
            patch["signature_status"] = sig
            patch["signature_note_ru"] = "Статус подписи ручной. Электронная подпись не подключена."
        if "finance_verify" in body:
            if not can(role, "finance"):
                return {"ok": False, "error": "forbidden", "message_ru": "Проверку платёжных документов выполняет бухгалтер"}
            ver = str(body.get("finance_verify") or "").upper()
            if ver not in FINANCE_VERIFY_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус проверки"}
            patch["finance_verify"] = ver
        if "ocr_confirm" in body and body.get("ocr_confirm"):
            draft = item.get("ocr_draft") or {}
            if isinstance(draft, dict) and draft.get("vin") and body.get("apply_vin"):
                return {"ok": False, "error": "validation", "message_ru": "VIN из файла не записывается в карточку авто без явного подтверждения поля apply_vehicle_vin"}
            patch["ocr_draft"] = {**(draft if isinstance(draft, dict) else {}), "confirmed": True}
        item.update(patch)
        await self._persist_update("document", document_id, patch)
        action = "document_approved" if patch.get("workflow_status") == "APPROVED" else "document_status"
        await self._audit(organization_id=org, action=action, entity_type="document", entity_id=document_id, role=role, actor_id=actor_id, old_value=old, new_value={k: patch.get(k) for k in patch if k != "updated_at"})
        if item.get("customs_id") and (patch.get("finance_verify") in {"VERIFIED", "CONFIRMED"} or patch.get("workflow_status") == "APPROVED"):
            await self._audit(
                organization_id=org,
                action="document_verified",
                entity_type="customs_case",
                entity_id=str(item.get("customs_id")),
                role=role,
                actor_id=actor_id,
                new_value={"document_id": document_id, "finance_verify": patch.get("finance_verify"), "workflow_status": patch.get("workflow_status")},
                summary="Документ растаможки проверен",
            )
        return {"ok": True, "item": self._public_document(org, item, role), "signature_provider": None}

    def status_transition_warning(self, org: str, vehicle: dict[str, Any], new_status: str) -> dict[str, Any] | None:
        if str(new_status).upper() not in {"READY_FOR_SALE", "RESERVED", "SOLD", "IN_UKRAINE"}:
            return None
        pack = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS if new_status != "IN_UKRAINE" else REGISTRATION_PACKAGE_ITEMS)
        missing = pack.get("missing") or []
        if not missing:
            return None
        return {
            "warning": True,
            "missing": missing,
            "message_ru": f"Не хватает {len(missing)} документов.",
        }

    def deal_close_warning(self, org: str, deal: dict[str, Any]) -> dict[str, Any] | None:
        reasons: list[str] = []
        if not deal.get("client_id"):
            reasons.append("Нет клиента")
        if not deal.get("vehicle_id"):
            reasons.append("Нет автомобиля")
        price = deal.get("sale_price") or deal.get("price")
        if price in (None, "", 0, "0"):
            reasons.append("Нет цены продажи")
        vehicle = self._find(org, "vehicles", str(deal.get("vehicle_id") or "")) if deal.get("vehicle_id") else None
        pack = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS) if vehicle else {"missing": ["пакет продажи"]}
        for m in pack.get("missing") or []:
            reasons.append(m)
        if reasons:
            return {"warning": True, "missing": reasons, "message_ru": f"Перед закрытием сделки: {'; '.join(reasons[:6])}"}
        return None

    def finance_document_flag(self, org: str, expense: dict[str, Any]) -> dict[str, Any]:
        vid = str(expense.get("vehicle_id") or "")
        eid = str(expense.get("id") or "")
        docs = self._active_docs(org, vid) if vid else []
        linked = [d for d in docs if str(d.get("payment_id") or "") == eid or str(d.get("document_type") or "") in {"invoice", "carrier_invoice", "port_invoice", "auction_invoice"}]
        if linked:
            return {"has_document": True, "note_ru": "Расход учтён"}
        return {"has_document": False, "note_ru": "Расход учтён. Документ отсутствует", "warning_ru": "Invoice missing"}

    async def document_alerts(self, organization_id: str, role: str | None = "auto_director") -> dict[str, Any]:
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        alerts: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).date()
        soon = now + timedelta(days=14)
        for v in self._bag(org)["vehicles"]:
            if str(v.get("status")) in {"CANCELLED", "INTEREST"}:
                continue
            sale = self._eval_package(org, v, SALE_PACKAGE_ITEMS)
            if sale.get("missing"):
                alerts.append({"kind": "sale_incomplete", "vehicle_id": v.get("id"), "message_ru": f"Пакет продажи не готов: {', '.join(sale['missing'][:4])}"})
            reg = self._eval_package(org, v, REGISTRATION_PACKAGE_ITEMS)
            if reg.get("missing") and str(v.get("status")) in {"CUSTOMS_CLEARED", "IN_UKRAINE", "PREPARATION", "READY_FOR_SALE"}:
                alerts.append({"kind": "registration_incomplete", "vehicle_id": v.get("id"), "message_ru": f"Пакет регистрации не готов: {', '.join(reg['missing'][:4])}"})
            customs_docs = [d for d in self._active_docs(org, str(v.get("id"))) if str(d.get("document_type")) == "customs_declaration"]
            if str(v.get("status")) in {"CUSTOMS", "DESTINATION_PORT"} and not customs_docs:
                alerts.append({"kind": "customs_incomplete", "vehicle_id": v.get("id"), "message_ru": "Не хватает таможенной декларации"})
        for d in self._active_docs(org):
            if str(d.get("finance_verify") or d.get("signature_status") or "") == "REJECTED":
                alerts.append({"kind": "rejected", "document_id": d.get("id"), "vehicle_id": d.get("vehicle_id"), "message_ru": "Документ отклонён"})
            until = str(d.get("valid_until") or "")[:10]
            if until:
                try:
                    day = datetime.fromisoformat(until).date()
                    if now <= day <= soon:
                        alerts.append({"kind": "expires_soon", "document_id": d.get("id"), "vehicle_id": d.get("vehicle_id"), "message_ru": "Документ скоро истекает"})
                except ValueError:
                    pass
        sent = 0
        for alert in alerts:
            await self.notify_telegram_staff(
                org,
                title=str(alert.get("message_ru") or "Документ"),
                entity_type="document_alert",
                entity_id=str(alert.get("document_id") or alert.get("vehicle_id") or "doc"),
                vehicle_id=str(alert["vehicle_id"]) if alert.get("vehicle_id") else None,
            )
            sent += 1
        return {"ok": True, "items": alerts, "sent": sent}

    def vin_link_warning(self, vehicle: dict[str, Any] | None, extracted_vin: str | None) -> dict[str, Any] | None:
        if not extracted_vin or not vehicle:
            return None
        if str(vehicle.get("vin") or "").upper() != extracted_vin.upper():
            return {
                "warning": True,
                "code": "vin_conflict",
                "extracted_vin": extracted_vin.upper(),
                "selected_vin": vehicle.get("vin"),
                "message_ru": "Извлечённый VIN не совпадает с выбранным автомобилем. Привязка не меняется автоматически.",
            }
        return None

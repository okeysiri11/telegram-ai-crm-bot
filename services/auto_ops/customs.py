"""AUTO 1.2 customs operating desk — cases, brokers, VAT, certification.

Mixin for AutoOpsService. Reuses AUTO 1.0 expenses, documents, photos, tasks, audit.
Rates are organization-configured. Never claimed as live Гостаможня / НБУ.
"""

from __future__ import annotations

import uuid
from typing import Any

from services.auto_ops.customs_catalog import (
    BROKER_TYPES,
    CASE_STATUSES,
    CASE_STATUS_IDS,
    CASE_STATUS_LABELS,
    CERT_STATUSES,
    CHECKLIST,
    CUSTOMS_EXPENSE_IDS,
    CUSTOMS_TABS,
    DEFAULT_RATES,
    NEXT_STAGE,
    REG_STATUSES,
    allowed_next_statuses,
    calculate_customs,
    is_backward_transition,
    normalize_case_status,
    pipeline_for_case,
    transition_allowed,
)
from services.auto_ops.rbac import can, normalize_role, require

BROKER_TYPE_IDS = frozenset(dict(BROKER_TYPES))
CERT_STATUS_IDS = frozenset(dict(CERT_STATUSES))
REG_STATUS_IDS = frozenset(dict(REG_STATUSES))
CERT_LABELS = dict(CERT_STATUSES)
REG_LABELS = dict(REG_STATUSES)

CUSTOMS_BAG_KEYS = ("customs_cases", "brokers", "customs_settings")

CLOSED_CASE = frozenset({"REGISTERED"})
PROBLEM_STATUS = frozenset({"ON_HOLD", "REJECTED"})

CASE_FIELDS = (
    "vehicle_id",
    "status",
    "broker_id",
    "customs_office",
    "declaration_number",
    "customs_value",
    "currency",
    "fx_rate_to_uah",
    "engine_cc",
    "fuel_type",
    "year",
    "broker_fee_uah",
    "location_current",
    "responsible_manager_id",
    "cert_status",
    "cert_body",
    "cert_number",
    "cert_date",
    "reg_status",
    "plate_expected",
    "mreo_office",
    "mreo_date",
    "registration_number",
    "manual_tax_override",
    "duty_uah",
    "excise_uah",
    "import_vat_uah",
    "state_total_uah",
    "grand_total_uah",
    "cleared_at",
    "registered_at",
    "notes",
    "is_demo",
    "workspace_id",
)

LOCATION_BY_STATUS = {
    "AWAITING_ARRIVAL": "В пути / ожидает прибытия на таможню",
    "DOCUMENTS_PREP": "Документы собираются",
    "SUBMITTED": "Подано брокеру / в таможню",
    "INSPECTION": "На осмотре",
    "DUTY_CALCULATION": "На расчёте платежей",
    "PAYMENT_PENDING": "Ожидает оплаты",
    "PAID": "Платежи проведены, ожидает выпуска",
    "CLEARED": "Выпущено с таможни",
    "CERTIFICATION": "На сертификации",
    "REGISTRATION_PREP": "Пакет в МРЕО готовится",
    "REGISTERED": "Зарегистрировано",
    "ON_HOLD": "На паузе",
    "REJECTED": "Отказ",
}


def _str(value: Any) -> str:
    return str(value or "").strip()


class AutoOpsCustomsMixin:
    """Customs / broker / VAT / certification desk. Expects AutoOpsService helpers."""

    def _customs_rates(self, org: str) -> dict[str, Any]:
        rows = self._bag(org).get("customs_settings") or []
        raw = rows[0] if rows else {}
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        merged = {**DEFAULT_RATES, **payload}
        for key in DEFAULT_RATES:
            if raw.get(key) not in (None, ""):
                merged[key] = raw[key]
        return merged

    def _active_case_for_vehicle(self, org: str, vehicle_id: str) -> dict[str, Any] | None:
        cases = [c for c in self._bag(org)["customs_cases"] if str(c.get("vehicle_id")) == str(vehicle_id)]
        cases.sort(key=lambda c: str(c.get("updated_at") or ""), reverse=True)
        return next((c for c in cases if str(c.get("status") or "").upper() not in CLOSED_CASE), cases[0] if cases else None)

    def _case_docs(self, org: str, case: dict[str, Any]) -> list[dict[str, Any]]:
        cid = str(case.get("id") or "")
        vid = str(case.get("vehicle_id") or "")
        return [
            d
            for d in self._bag(org)["documents"]
            if not d.get("archived_at")
            and (
                str(d.get("customs_id") or "") == cid
                or (vid and str(d.get("vehicle_id") or "") == vid)
            )
        ]

    def _checklist_for(self, org: str, case: dict[str, Any]) -> dict[str, Any]:
        docs = self._case_docs(org, case)
        by_type: dict[str, list[dict[str, Any]]] = {}
        for doc in docs:
            by_type.setdefault(str(doc.get("document_type") or "other"), []).append(doc)
        items: list[dict[str, Any]] = []
        missing: list[dict[str, str]] = []
        for row in CHECKLIST:
            dtype = row["document_type"]
            found = by_type.get(dtype) or []
            # Title also matches title_copy presence separately.
            present = bool(found)
            preview = None
            if found:
                file_id = found[0].get("file_id")
                preview = {
                    "document_id": found[0].get("id"),
                    "file_id": file_id,
                    "file_name": found[0].get("file_name"),
                    "title": found[0].get("title"),
                }
            item = {**row, "present": present, "documents": found, "preview": preview}
            items.append(item)
            if not present:
                missing.append({"id": row["id"], "document_type": dtype, "label_ru": row["label_ru"]})
        return {
            "items": items,
            "missing": missing,
            "complete": not missing,
            "present_count": sum(1 for i in items if i["present"]),
            "required_count": len(items),
        }

    def _customs_payments(self, org: str, case: dict[str, Any], role: str | None) -> dict[str, Any]:
        if not can(role, "finance"):
            return {"restricted": True, "message_ru": "Суммы доступны директору и бухгалтеру."}
        cid = str(case.get("id") or "")
        vid = str(case.get("vehicle_id") or "")
        planned = paid = unpaid = 0.0
        by_currency: dict[str, dict[str, float]] = {}
        lines: list[dict[str, Any]] = []
        vat_paid = 0.0
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("payment_status") or "") == "cancelled":
                continue
            cat = str(exp.get("category") or "")
            if cat not in CUSTOMS_EXPENSE_IDS:
                continue
            linked = str(exp.get("customs_id") or "") == cid or (not exp.get("customs_id") and str(exp.get("vehicle_id") or "") == vid)
            if not linked:
                continue
            base = self._expense_base(exp)
            cur = str(exp.get("currency") or "USD").upper()
            bucket = by_currency.setdefault(cur, {"planned": 0.0, "paid": 0.0, "unpaid": 0.0})
            status = str(exp.get("payment_status") or "paid")
            if status == "planned":
                planned += base
                bucket["planned"] += base
            elif status == "paid":
                paid += base
                bucket["paid"] += base
                if cat == "IMPORT_VAT":
                    vat_paid += base
            else:
                unpaid += base
                bucket["unpaid"] += base
            lines.append(exp)
        due = round(planned + unpaid, 2)
        return {
            "planned": round(planned, 2),
            "paid": round(paid, 2),
            "unpaid": round(unpaid, 2),
            "due": due,
            "remaining": due,
            "currency": "UAH",
            "display_currency": "UAH",
            "fx_source_label_ru": "Введено вручную",
            "from_records": True,
            "by_currency": {k: {ik: round(iv, 2) for ik, iv in v.items()} for k, v in by_currency.items()},
            "import_vat_paid": round(vat_paid, 2),
            "lines": lines,
        }

    def _run_calculation(self, org: str, case: dict[str, Any], vehicle: dict[str, Any] | None) -> dict[str, Any]:
        rates = self._customs_rates(org)
        year = case.get("year") if case.get("year") not in (None, "") else (vehicle or {}).get("year")
        fuel = case.get("fuel_type") or (vehicle or {}).get("fuel_type")
        engine_cc = case.get("engine_cc")
        if engine_cc in (None, "") and (vehicle or {}).get("engine"):
            raw = str(vehicle.get("engine") or "")
            digits = "".join(ch if ch.isdigit() or ch == "." else " " for ch in raw).split()
            if digits:
                try:
                    engine_cc = float(digits[0])
                except ValueError:
                    engine_cc = None
        return calculate_customs(
            customs_value=case.get("customs_value"),
            currency=str(case.get("currency") or "USD"),
            fx_rate_to_uah=case.get("fx_rate_to_uah"),
            engine_cc=engine_cc,
            fuel_type=str(fuel) if fuel else None,
            year=year,
            broker_fee_uah=case.get("broker_fee_uah") or 0,
            rates=rates,
        )

    def _todo_list(self, case: dict[str, Any], checklist: dict[str, Any], calc: dict[str, Any], payments: dict[str, Any]) -> list[str]:
        status = str(case.get("status") or "").upper()
        todos: list[str] = []
        if checklist.get("missing"):
            todos.append("Загрузить недостающие документы")
        if not calc.get("ok"):
            todos.append("Заполнить таможенную стоимость, курс и объём двигателя")
        if status in {"DUTY_CALCULATION", "DOCUMENTS_PREP", "SUBMITTED", "INSPECTION"} and calc.get("ok"):
            todos.append("Подтвердить расчёт и перейти к оплате")
        if status == "PAYMENT_PENDING" or (not payments.get("restricted") and (payments.get("due") or 0) > 0 and status not in CLOSED_CASE | {"PAID", "CLEARED", "CERTIFICATION", "REGISTRATION_PREP", "REGISTERED"}):
            todos.append("Оплатить мито / акциз / НДС")
        if status in {"PAID", "CLEARED"} or (status == "CERTIFICATION" and str(case.get("cert_status") or "NOT_STARTED") != "CERTIFIED"):
            todos.append("Получить сертификат соответствия")
        if status in {"CERTIFICATION", "REGISTRATION_PREP"} and str(case.get("reg_status") or "NOT_READY") not in {"REGISTERED"}:
            todos.append("Собрать пакет для МРЕО")
        if status == "ON_HOLD":
            todos.append("Снять паузу и продолжить")
        if status == "REJECTED":
            todos.append("Разобрать отказ и подать заново")
        if not todos:
            next_id = NEXT_STAGE.get(status)
            if next_id and next_id != status:
                todos.append(f"Перейти к этапу: {CASE_STATUS_LABELS.get(next_id, next_id)}")
        return todos

    def _answers(self, org: str, case: dict[str, Any], role: str | None, vehicle: dict[str, Any] | None, checklist: dict[str, Any], calc: dict[str, Any], payments: dict[str, Any]) -> dict[str, Any]:
        status = str(case.get("status") or "").upper()
        broker = self._find(org, "brokers", str(case.get("broker_id") or "")) if case.get("broker_id") else None
        responsible = (
            (broker or {}).get("company_name")
            or case.get("responsible_manager_id")
            or (vehicle or {}).get("assigned_manager_id")
            or "—"
        )
        where = case.get("location_current") or (vehicle or {}).get("location_current") or LOCATION_BY_STATUS.get(status, "—")
        next_id = NEXT_STAGE.get(status, status)
        missing = [m["label_ru"] for m in checklist.get("missing") or []]
        to_pay = None
        paid = None
        if not payments.get("restricted"):
            grand = calc.get("grand_total_uah") if calc.get("ok") else None
            paid_amt = payments.get("paid") or 0
            paid = paid_amt
            if grand is not None:
                to_pay = round(max(float(grand) - float(paid_amt), 0), 2)
            else:
                to_pay = payments.get("due")
        return {
            "where": where,
            "happening": CASE_STATUS_LABELS.get(status, status),
            "todo": self._todo_list(case, checklist, calc, payments),
            "missing_documents": missing,
            "to_pay": to_pay,
            "paid": paid,
            "responsible": responsible,
            "next_stage": CASE_STATUS_LABELS.get(next_id, next_id),
            "next_stage_id": next_id,
            "currency": "UAH",
        }

    def _public_case(self, org: str, case: dict[str, Any], role: str | None) -> dict[str, Any]:
        vehicle = self._find(org, "vehicles", str(case.get("vehicle_id") or ""))
        status = str(case.get("status") or "")
        broker = self._find(org, "brokers", str(case.get("broker_id") or "")) if case.get("broker_id") else None
        checklist = self._checklist_for(org, case)
        calc = self._run_calculation(org, case, vehicle)
        payments = self._customs_payments(org, case, role)
        answers = self._answers(org, case, role, vehicle, checklist, calc, payments)
        finance_ok = can(role, "finance")
        accounting = None
        if finance_ok:
            accounting = {
                "calculation": calc,
                "payments": payments,
                "vat": {
                    "calculated_uah": calc.get("import_vat_uah") if calc.get("ok") else None,
                    "paid": payments.get("import_vat_paid"),
                    "rate": calc.get("vat_rate") if calc.get("ok") else self._customs_rates(org).get("vat_rate"),
                    "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
                },
                "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
            }
        else:
            accounting = {"restricted": True, "message_ru": "Бухгалтерский разрез доступен директору и бухгалтеру."}
        return {
            **case,
            "status_ru": CASE_STATUS_LABELS.get(status, status),
            "vehicle_title": self._vehicle_title(vehicle) if vehicle else "",
            "vin": (vehicle or {}).get("vin"),
            "cover_file_id": self._cover_file(org, vehicle) if vehicle else None,
            "broker_name": (broker or {}).get("company_name") or "",
            "pipeline": pipeline_for_case(status),
            "checklist": checklist,
            "calculation": calc if finance_ok else {"restricted": True},
            "payments": payments,
            "answers": answers,
            "accounting": accounting,
            "certification": {
                "status": case.get("cert_status") or "NOT_STARTED",
                "status_ru": CERT_LABELS.get(str(case.get("cert_status") or "NOT_STARTED"), "Не начата"),
                "body": case.get("cert_body"),
                "number": case.get("cert_number"),
                "date": case.get("cert_date"),
            },
            "registration": {
                "status": case.get("reg_status") or "NOT_READY",
                "status_ru": REG_LABELS.get(str(case.get("reg_status") or "NOT_READY"), "Пакет не готов"),
                "plate_expected": case.get("plate_expected"),
                "mreo_office": case.get("mreo_office"),
                "mreo_date": case.get("mreo_date"),
            },
            "timeline": self._case_timeline(org, case),
            "rate_source_label_ru": "Ставка организации",
            "fx_source_label_ru": "Введено вручную",
            "official_calculator": False,
            "live_customs_api": False,
            "allowed_next": allowed_next_statuses(status, telegram=False),
            "allowed_next_telegram": allowed_next_statuses(status, telegram=True),
            "allowed_next_ru": [
                {"id": s, "label_ru": CASE_STATUS_LABELS.get(s, s)} for s in allowed_next_statuses(status, telegram=False)
            ],
        }

    def _case_timeline(self, org: str, case: dict[str, Any]) -> list[dict[str, Any]]:
        cid = str(case.get("id") or "")
        vid = str(case.get("vehicle_id") or "")
        events = [
            a
            for a in self._bag(org)["audit"]
            if str(a.get("entity_id") or "") in {cid, vid} or str(a.get("entity_type") or "") in {"customs_case", "broker"}
        ]
        events.sort(key=lambda a: str(a.get("created_at") or ""), reverse=True)
        out: list[dict[str, Any]] = []
        for a in events[:40]:
            out.append(
                {
                    "id": a.get("id"),
                    "at": a.get("created_at"),
                    "action": a.get("action"),
                    "summary": a.get("summary") or a.get("action"),
                    "actor": a.get("actor_id"),
                }
            )
        return out

    def vehicle_customs_block(self, org: str, vehicle_id: str, role: str | None) -> dict[str, Any]:
        cases = [c for c in self._bag(org)["customs_cases"] if str(c.get("vehicle_id")) == str(vehicle_id)]
        cases.sort(key=lambda c: str(c.get("updated_at") or ""), reverse=True)
        current = self._active_case_for_vehicle(org, vehicle_id)
        if not current:
            return {"case": None, "cases": [], "message_ru": "Дело растаможки ещё не создано."}
        pub = self._public_case(org, current, role)
        return {
            "case": pub,
            "cases": [self._public_case(org, c, role) for c in cases],
            "summary": self.customs_printable_summary(org, current, role),
        }

    async def list_customs_cases(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        q = query or {}
        scoped = self._scoped_rows(org, self._bag(org)["customs_cases"], q)
        items = [self._public_case(org, c, role) for c in scoped]
        tab = (q.get("tab") or "all").strip()
        tab_def = next((t for t in CUSTOMS_TABS if t["id"] == tab), CUSTOMS_TABS[0])
        if tab_def.get("statuses"):
            wanted = set(tab_def["statuses"])
            items = [c for c in items if str(c.get("status")) in wanted]
        status = (q.get("status") or "").strip().upper()
        broker = (q.get("broker") or q.get("broker_id") or "").strip()
        manager = (q.get("manager") or q.get("responsible_manager_id") or "").strip()
        search = (q.get("q") or q.get("search") or "").strip().upper()
        if status:
            items = [c for c in items if str(c.get("status")) == status]
        if broker:
            items = [c for c in items if str(c.get("broker_id") or "") == broker or broker.lower() in str(c.get("broker_name") or "").lower()]
        if manager:
            items = [c for c in items if str(c.get("responsible_manager_id") or "") == manager]
        if search:
            items = [c for c in items if search in self._case_search_hay(org, self._find(org, "customs_cases", str(c.get("id") or "")) or c)]
        all_pub = [self._public_case(org, c, role) for c in scoped]
        counts = {t["id"]: 0 for t in CUSTOMS_TABS}
        for t in CUSTOMS_TABS:
            if t.get("statuses"):
                wanted = set(t["statuses"])
                counts[t["id"]] = sum(1 for c in all_pub if str(c.get("status")) in wanted)
            else:
                counts[t["id"]] = len(all_pub)
        return {
            "ok": True,
            "items": items,
            "total": len(items),
            "counts": counts,
            "tabs": CUSTOMS_TABS,
            "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
        }

    async def get_customs_case(self, organization_id: str, case_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        case = self._find(org, "customs_cases", case_id)
        if not case:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        ws = self._workspace_id(org, query) if query and query.get("workspace_id") not in (None, "") else None
        if ws is not None and str(case.get("workspace_id") or org) != ws:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        pub = self._public_case(org, case, role)
        docs = self._case_docs(org, case)
        tasks = [t for t in self._bag(org)["tasks"] if str(t.get("customs_id") or "") == str(case_id) or str(t.get("vehicle_id") or "") == str(case.get("vehicle_id") or "")]
        return {
            "ok": True,
            "item": pub,
            "documents": docs,
            "tasks": tasks,
            "summary": self.customs_printable_summary(org, case, role),
            "broker": self._find(org, "brokers", str(case.get("broker_id") or "")) if case.get("broker_id") else None,
        }

    async def create_customs_case(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle_id = _str(body.get("vehicle_id"))
        vehicle = self._find(org, "vehicles", vehicle_id) if vehicle_id else None
        if not vehicle:
            return {"ok": False, "error": "validation", "message_ru": "Дело должно быть привязано к существующему автомобилю"}
        existing = self._active_case_for_vehicle(org, vehicle_id)
        if existing and str(existing.get("status") or "").upper() not in CLOSED_CASE and not body.get("reassign"):
            return {
                "ok": False,
                "error": "conflict",
                "message_ru": "У автомобиля уже есть открытое дело растаможки. Передайте reassign=true, чтобы закрыть его.",
                "existing_id": existing.get("id"),
            }
        if existing and body.get("reassign") and str(existing.get("status") or "").upper() not in CLOSED_CASE:
            existing["status"] = "ON_HOLD"
            existing["updated_at"] = self._now()
            await self._persist_update("customs_case", str(existing["id"]), {"status": "ON_HOLD", "updated_at": existing["updated_at"]})
        status = normalize_case_status(body.get("status") or "DOCUMENTS_PREP")
        if status not in CASE_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус дела", "field": "status"}
        item: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": self._workspace_id(org, body=body),
            "vehicle_id": vehicle_id,
            "status": status,
            "currency": _str(body.get("currency") or "USD").upper() or "USD",
            "cert_status": _str(body.get("cert_status") or "NOT_STARTED").upper() or "NOT_STARTED",
            "reg_status": _str(body.get("reg_status") or "NOT_READY").upper() or "NOT_READY",
            "year": body.get("year") if body.get("year") not in (None, "") else vehicle.get("year"),
            "fuel_type": body.get("fuel_type") or vehicle.get("fuel_type"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
            "is_demo": bool(body.get("is_demo")),
        }
        for field in CASE_FIELDS:
            if field in body and body[field] not in (None, "") and field not in {"vehicle_id", "status"}:
                item[field] = body[field]
        saved = await self._persist("customs_case", item)
        self._bag(org)["customs_cases"].insert(0, saved)
        await self._audit(
            organization_id=org,
            action="customs_case_created",
            entity_type="customs_case",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"vehicle_id": vehicle_id, "status": status},
            summary="Создано дело растаможки",
        )
        return {"ok": True, "item": self._public_case(org, saved, role)}

    async def update_customs_case(self, organization_id: str, case_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        correction = self._correction_payload(body)
        telegram_mode = bool(body.get("telegram") or body.get("telegram_strict"))
        denied = self._write_denied(role)
        if denied and not (correction and can(role, "admin")):
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "customs_cases", case_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        old_status = str(item.get("status") or "")
        old_broker = item.get("broker_id")
        old_decl = item.get("declaration_number")
        old_cert = item.get("cert_number")
        old_reg = item.get("reg_status")
        patch: dict[str, Any] = {}
        if "status" in body:
            status = normalize_case_status(body.get("status"))
            if status not in CASE_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус дела", "field": "status"}
            if not transition_allowed(old_status, status, telegram=telegram_mode):
                if not correction:
                    return {
                        "ok": False,
                        "error": "validation",
                        "message_ru": "Недопустимый переход статуса. Исправление истории — только в режиме коррекции с причиной и датой.",
                        "field": "status",
                        "from": old_status,
                        "to": status,
                        "backward": is_backward_transition(old_status, status),
                    }
                if not can(role, "admin"):
                    return {"ok": False, "error": "forbidden", "message_ru": "Коррекцию исторического статуса выполняет директор или администратор"}
            patch["status"] = status
            if status == "CLEARED" and not item.get("cleared_at"):
                patch["cleared_at"] = self._now()
            if status == "REGISTERED" and not item.get("registered_at"):
                patch["registered_at"] = self._now()
        if "cert_status" in body:
            cs = _str(body.get("cert_status")).upper()
            if cs not in CERT_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус сертификации", "field": "cert_status"}
            patch["cert_status"] = cs
        if "reg_status" in body:
            rs = _str(body.get("reg_status")).upper()
            if rs not in REG_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус регистрации", "field": "reg_status"}
            patch["reg_status"] = rs
        for field in CASE_FIELDS:
            if field in body and field not in {"status", "cert_status", "reg_status", "vehicle_id"}:
                patch[field] = body[field]
        if body.get("manual_tax_override") or body.get("override_duty_uah") not in (None, "") or body.get("override_excise_uah") not in (None, "") or body.get("override_vat_uah") not in (None, ""):
            patch["manual_tax_override"] = True
            for key in ("override_duty_uah", "override_excise_uah", "override_vat_uah"):
                if body.get(key) not in (None, ""):
                    patch[key] = body[key]
        patch["updated_at"] = self._now()
        patch["updated_by"] = actor_id or normalize_role(role)
        if correction and patch.get("status") and patch["status"] != old_status:
            patch["correction"] = correction
        item.update(patch)
        await self._persist_update("customs_case", case_id, patch)
        action = "customs_case_updated"
        extra_audits: list[tuple[str, str]] = []
        if patch.get("status") and patch["status"] != old_status:
            action = "customs_status_corrected" if correction else "customs_status_changed"
            extra_audits.append((action, "Изменён статус растаможки"))
            if patch["status"] == "CLEARED":
                extra_audits.append(("customs_cleared", "Выпуск с таможни"))
            if patch["status"] == "REGISTERED":
                extra_audits.append(("registration_completed", "Регистрация завершена"))
        if "broker_id" in patch and patch.get("broker_id") != old_broker:
            extra_audits.append(("customs_broker_changed", "Назначен брокер"))
            extra_audits.append(("broker_assigned", "Назначен брокер"))
        if "declaration_number" in patch and patch.get("declaration_number") not in (None, "") and patch.get("declaration_number") != old_decl:
            extra_audits.append(("declaration_entered", "Введена декларация"))
        if patch.get("manual_tax_override"):
            extra_audits.append(("customs_tax_override", "Ручная корректировка платежей"))
        elif any(k in patch for k in ("customs_value", "fx_rate_to_uah", "engine_cc", "broker_fee_uah")):
            extra_audits.append(("customs_calculation_changed", "Пересчитаны таможенные платежи"))
        if "cert_number" in patch and patch.get("cert_number") not in (None, "") and patch.get("cert_number") != old_cert:
            extra_audits.append(("certificate_added", "Добавлен сертификат"))
        elif any(k.startswith("cert_") for k in patch):
            extra_audits.append(("certification_updated", "Обновлена сертификация"))
        if patch.get("reg_status") == "REGISTERED" and old_reg != "REGISTERED":
            extra_audits.append(("registration_completed", "Регистрация завершена"))
        elif any(k in patch for k in ("reg_status", "plate_expected", "mreo_office", "mreo_date", "registration_number")):
            extra_audits.append(("registration_updated", "Обновлена регистрация"))
        if not extra_audits:
            extra_audits.append((action, action))
        for act, summary in extra_audits:
            await self._audit(
                organization_id=org,
                action=act,
                entity_type="customs_case",
                entity_id=case_id,
                role=role,
                actor_id=actor_id,
                old_value={"status": old_status, **({"correction": None} if correction else {})},
                new_value={k: patch.get(k) for k in patch if k not in {"updated_at", "updated_by"}},
                summary=summary,
            )
        return {"ok": True, "item": self._public_case(org, item, role), "correction": bool(correction)}

    async def calculate_customs_case(self, organization_id: str, case_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "edit") or can(role, "create") or can(role, "finance")):
            return require(role, "edit")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "customs_cases", case_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        patch = {k: body[k] for k in ("customs_value", "currency", "fx_rate_to_uah", "engine_cc", "fuel_type", "year", "broker_fee_uah") if k in body}
        if patch:
            patch["updated_at"] = self._now()
            item.update(patch)
            await self._persist_update("customs_case", case_id, patch)
        calc = self._run_calculation(org, item, self._find(org, "vehicles", str(item.get("vehicle_id") or "")))
        snap = {}
        if calc.get("ok"):
            snap = {
                "duty_uah": calc.get("duty_uah"),
                "excise_uah": calc.get("excise_uah"),
                "import_vat_uah": calc.get("import_vat_uah"),
                "state_total_uah": calc.get("state_total_uah"),
                "grand_total_uah": calc.get("grand_total_uah"),
                "updated_at": self._now(),
            }
            item.update(snap)
            await self._persist_update("customs_case", case_id, snap)
        await self._audit(
            organization_id=org,
            action="customs_calculation_changed",
            entity_type="customs_case",
            entity_id=case_id,
            role=role,
            actor_id=actor_id,
            new_value={"ok": calc.get("ok"), "incomplete": calc.get("incomplete")},
            summary="Пересчитаны таможенные платежи",
        )
        if body.get("manual_tax_override") or any(k in body for k in ("override_duty_uah", "override_excise_uah", "override_vat_uah")):
            await self._audit(
                organization_id=org,
                action="customs_tax_override",
                entity_type="customs_case",
                entity_id=case_id,
                role=role,
                actor_id=actor_id,
                new_value={"manual_tax_override": True},
                summary="Ручная корректировка платежей",
            )
        return {"ok": True, "item": self._public_case(org, item, role), "calculation": calc}

    async def create_broker(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        btype = _str(body.get("type") or "customs_broker").lower()
        if btype not in BROKER_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип брокера", "field": "type"}
        return await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="broker",
            bag_key="brokers",
            required=("company_name",),
            fields=("company_name", "type", "country", "contact_person", "phone", "email", "telegram", "tax_id", "notes", "rating", "active"),
            defaults={"type": btype, "active": True},
            body={**body, "type": btype},
            audit_action="broker_created",
        )

    async def list_brokers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        return await self._simple_list(organization_id, role, "brokers", query, ("company_name", "country", "type"))

    async def update_broker(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        return await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="broker",
            bag_key="brokers",
            fields=("company_name", "type", "country", "contact_person", "phone", "email", "telegram", "tax_id", "notes", "rating", "active"),
            missing_ru="Брокер не найден",
        )

    async def customs_settings(self, organization_id: str, role: str | None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        if body is not None:
            if not can(role, "admin"):
                return require(role, "admin")
            rows = self._bag(org)["customs_settings"]
            rates = {k: body[k] for k in DEFAULT_RATES if k in body}
            if rows:
                item = rows[0]
                payload = {**(item.get("payload") or {}), **rates}
                item["payload"] = payload
                item.update(rates)
                item["updated_at"] = self._now()
                await self._persist_update("customs_setting", str(item["id"]), {"payload": payload, "updated_at": item["updated_at"]})
            else:
                item = {
                    "id": str(uuid.uuid4()),
                    "organization_id": org,
                    "tenant_id": org,
                    "payload": rates,
                    "created_at": self._now(),
                    "updated_at": self._now(),
                }
                saved = await self._persist("customs_setting", item)
                self._bag(org)["customs_settings"].insert(0, saved)
            await self._audit(organization_id=org, action="customs_rates_updated", entity_type="customs_setting", entity_id="org", role=role, new_value=rates, summary="Обновлены ставки организации")
        return {
            "ok": True,
            "rates": self._customs_rates(org),
            "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
            "live_customs_api": False,
            "live_nbu_fx": False,
            "official_calculator": False,
            "catalogs": {
                "statuses": [{"id": i, "label_ru": l} for i, l in CASE_STATUSES],
                "checklist": CHECKLIST,
                "broker_types": [{"id": i, "label_ru": l} for i, l in BROKER_TYPES],
            },
        }

    async def seed_demo_customs(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not body.get("confirm_demo"):
            return {"ok": False, "error": "validation", "message_ru": "Для демо-сценария передайте confirm_demo=true. Демо никогда не смешивается с продакшен-записями без явного флага."}
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle = await self.create_vehicle(
            org,
            {
                "vin": "WBAFR9C50DD654321",
                "allow_nonstandard_vin": True,
                "manufacturer": "BMW",
                "model": "X5",
                "year": 2013,
                "fuel_type": "petrol",
                "engine": "2993",
                "purchase_country": "US",
                "auction_name": "Copart (demo)",
                "auction_url": "https://demo.invalid/lot/x5-customs",
                "status": "CUSTOMS",
                "location_current": "Одесса, таможня (demo)",
                "origin_port": "Savannah",
                "destination_port": "Odesa",
                "assigned_manager_id": "demo-manager",
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
            vrow["notes"] = "DEMO — AUTO 1.2 customs scenario. Not a production record."
        broker = await self.create_broker(
            org,
            {"company_name": "DEMO Customs Broker LLC", "type": "customs_broker", "country": "UA", "phone": "+38000000000", "is_demo": True},
            role,
            actor_id,
        )
        bid = str((broker.get("item") or {}).get("id") or "")
        case = await self.create_customs_case(
            org,
            {
                "vehicle_id": vid,
                "status": "PAYMENT_PENDING",
                "broker_id": bid,
                "customs_office": "Одесса (demo)",
                "customs_value": 18500,
                "currency": "USD",
                "fx_rate_to_uah": 41.5,
                "engine_cc": 2993,
                "fuel_type": "petrol",
                "year": 2013,
                "broker_fee_uah": 8000,
                "location_current": "Одесса, таможня (demo)",
                "responsible_manager_id": "demo-manager",
                "cert_status": "NOT_STARTED",
                "reg_status": "NOT_READY",
                "is_demo": True,
                "notes": "DEMO USA → Ukraine customs. Missing MD / certificate / registration.",
            },
            role,
            actor_id,
        )
        if not case.get("ok"):
            return case
        cid = str(case["item"]["id"])
        await self.calculate_customs_case(org, cid, {}, role, actor_id)
        for dtype, fname in (
            ("invoice", "demo-invoice.pdf"),
            ("title", "demo-title.pdf"),
            ("bill_of_lading", "demo-bl.pdf"),
            ("packing_list", "demo-packing.pdf"),
            ("export_document", "demo-export.pdf"),
        ):
            await self.create_document(
                org,
                {"owner_type": "customs", "customs_id": cid, "vehicle_id": vid, "file_name": fname, "document_type": dtype, "title": fname},
                role,
                actor_id,
            )
        await self.create_expense(
            org,
            {
                "vehicle_id": vid,
                "customs_id": cid,
                "category": "BROKER",
                "amount": 8000,
                "currency": "UAH",
                "exchange_rate": 1,
                "payment_status": "paid",
                "description": "DEMO broker fee",
            },
            "auto_accountant",
            actor_id,
        )
        await self.create_expense(
            org,
            {
                "vehicle_id": vid,
                "customs_id": cid,
                "category": "DUTY",
                "amount": 76775,
                "currency": "UAH",
                "exchange_rate": 1,
                "payment_status": "planned",
                "description": "DEMO duty",
            },
            "auto_accountant",
            actor_id,
        )
        await self.create_task(org, {"title": "Оплатить мито и НДС (demo)", "vehicle_id": vid, "customs_id": cid, "priority": "high"}, role, actor_id)
        crow = self._find(org, "customs_cases", cid)
        if crow:
            crow["is_demo"] = True
        brow = self._find(org, "brokers", bid)
        if brow:
            brow["is_demo"] = True
        refreshed = await self.get_customs_case(org, cid, role)
        return {
            "ok": True,
            "demo": True,
            "label_ru": "Демо-сценарий AUTO 1.2. Не продакшен.",
            "vehicle": vehicle.get("item"),
            "case": (refreshed.get("item") if refreshed.get("ok") else case.get("item")),
            "broker": broker.get("item"),
        }

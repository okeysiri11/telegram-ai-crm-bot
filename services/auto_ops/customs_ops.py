"""AUTO 1.8 customs operations — payments, summary, correction helpers.

Mixin for AutoOpsService. Reuses 1.2 cases and 1.0 expenses. Never a second cash ledger.
"""

from __future__ import annotations

from typing import Any

from services.auto_ops.customs_catalog import CHARGE_IDS, CUSTOMS_EXPENSE_IDS, DEFAULT_RATES
from services.auto_ops.rbac import can, require


def _str(value: Any) -> str:
    return str(value or "").strip()


class AutoOpsCustomsOpsMixin:
    """Printable summary + customs expense payments that stay planned until confirm."""

    def _correction_payload(self, body: dict[str, Any]) -> dict[str, Any] | None:
        raw = body.get("correction") if isinstance(body.get("correction"), dict) else None
        reason = _str((raw or {}).get("reason") or body.get("correction_reason") or body.get("reason"))
        at = _str((raw or {}).get("timestamp") or (raw or {}).get("corrected_at") or body.get("correction_at") or body.get("corrected_at"))
        if not reason or not at:
            return None
        return {"reason": reason, "timestamp": at, "mode": "admin_correction"}

    def customs_printable_summary(self, org: str, case: dict[str, Any], role: str | None) -> dict[str, Any]:
        pub = self._public_case(org, case, role)
        vehicle = self._find(org, "vehicles", str(case.get("vehicle_id") or ""))
        finance_ok = can(role, "finance")
        answers = pub.get("answers") or {}
        calc = pub.get("calculation") or {}
        payments = pub.get("payments") or {}
        out: dict[str, Any] = {
            "title_ru": "Сводка по растаможке",
            "vehicle": pub.get("vehicle_title") or self._vehicle_title(vehicle) if vehicle else "",
            "vin": pub.get("vin") or (vehicle or {}).get("vin"),
            "broker": pub.get("broker_name") or "",
            "declaration": case.get("declaration_number") or "",
            "status": pub.get("status"),
            "status_ru": pub.get("status_ru"),
            "customs_office": case.get("customs_office"),
            "next_stage": answers.get("next_stage"),
            "plate_expected": case.get("plate_expected"),
            "registration_number": case.get("registration_number"),
            "live_customs_api": False,
            "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
        }
        if finance_ok and not payments.get("restricted"):
            out["to_pay"] = answers.get("to_pay")
            out["paid"] = answers.get("paid")
            if calc.get("ok"):
                out["duty_uah"] = calc.get("duty_uah")
                out["excise_uah"] = calc.get("excise_uah")
                out["import_vat_uah"] = calc.get("import_vat_uah")
                out["grand_total_uah"] = calc.get("grand_total_uah")
        return out

    async def get_customs_summary(self, organization_id: str, case_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
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
        return {"ok": True, "item": self.customs_printable_summary(org, case, role), "title_ru": "Сводка по растаможке"}

    async def add_customs_payment(self, organization_id: str, case_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "finance_write") or can(role, "create") or can(role, "edit")):
            return require(role, "finance_write") or {"ok": False, "error": "forbidden"}
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        case = self._find(org, "customs_cases", case_id)
        if not case:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        category = _str(body.get("category") or body.get("charge") or "DUTY").upper()
        if category not in CHARGE_IDS and category not in CUSTOMS_EXPENSE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестная статья платежа", "field": "category"}
        created = await self.create_expense(
            org,
            {
                "vehicle_id": case.get("vehicle_id"),
                "customs_id": case_id,
                "category": category,
                "amount": body.get("amount"),
                "currency": body.get("currency") or "UAH",
                "description": body.get("comment") or body.get("description"),
                "document_id": body.get("document_id"),
                "workspace_id": case.get("workspace_id") or org,
                "payment_status": "planned",
            },
            role,
            actor_id,
        )
        if not created.get("ok"):
            return created
        await self._audit(
            organization_id=org,
            action="customs_payment_added",
            entity_type="customs_case",
            entity_id=case_id,
            role=role,
            actor_id=actor_id,
            new_value={
                "expense_id": created["item"]["id"],
                "category": category,
                "amount": created["item"].get("amount"),
                "payment_status": "planned",
            },
            summary="Платёж растаможки добавлен (не подтверждён)",
        )
        return {
            "ok": True,
            "item": created["item"],
            "confirmed": False,
            "message_ru": "Платёж записан как запланированный. Подтверждение — отдельный шаг.",
        }

    async def confirm_customs_payment(self, organization_id: str, case_id: str, expense_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not can(role, "finance_write"):
            return require(role, "finance_write") or {"ok": False, "error": "forbidden"}
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        case = self._find(org, "customs_cases", case_id)
        if not case:
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        exp = self._find(org, "expenses", expense_id)
        if not exp or str(exp.get("customs_id") or "") != str(case_id):
            return {"ok": False, "error": "not_found", "message_ru": "Платёж растаможки не найден"}
        if str(exp.get("payment_status") or "") in {"paid", "confirmed"}:
            return {"ok": True, "item": exp, "confirmed": True, "message_ru": "Платёж уже подтверждён", "duplicate": True}
        updated = await self.update_expense(
            org,
            expense_id,
            {"payment_status": "paid", "payment_date": body.get("payment_date") or body.get("timestamp") or self._now()[:10]},
            role,
            actor_id,
        )
        if not updated.get("ok"):
            return updated
        await self._audit(
            organization_id=org,
            action="customs_payment_confirmed",
            entity_type="customs_case",
            entity_id=case_id,
            role=role,
            actor_id=actor_id,
            new_value={"expense_id": expense_id, "payment_status": "paid"},
            summary="Платёж растаможки подтверждён",
        )
        return {"ok": True, "item": updated["item"], "confirmed": True, "message_ru": "Платёж подтверждён"}

    def _case_search_hay(self, org: str, case: dict[str, Any]) -> str:
        vehicle = self._find(org, "vehicles", str(case.get("vehicle_id") or ""))
        broker = self._find(org, "brokers", str(case.get("broker_id") or "")) if case.get("broker_id") else None
        client = None
        if vehicle and vehicle.get("client_id"):
            client = self._find(org, "clients", str(vehicle.get("client_id")))
        doc_nums = [
            str(d.get("document_number") or d.get("file_name") or "")
            for d in self._bag(org)["documents"]
            if not d.get("archived_at")
            and (
                str(d.get("customs_id") or "") == str(case.get("id") or "")
                or str(d.get("vehicle_id") or "") == str(case.get("vehicle_id") or "")
            )
        ]
        parts = [
            (vehicle or {}).get("vin"),
            self._vehicle_title(vehicle) if vehicle else "",
            case.get("declaration_number"),
            case.get("registration_number"),
            case.get("plate_expected"),
            (vehicle or {}).get("plate") or (vehicle or {}).get("license_plate"),
            (broker or {}).get("company_name"),
            (client or {}).get("name"),
            case.get("customs_office"),
            " ".join(doc_nums),
        ]
        return " ".join(str(p or "") for p in parts).upper()

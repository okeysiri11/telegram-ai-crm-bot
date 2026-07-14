# Partner Cabinet v1 self-test.

from __future__ import annotations


def run_partner_cabinet_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_partner_cabinet_v1 import PartnerCabinetV1

        checks["engine"] = {
            "ok": hasattr(PartnerCabinetV1, "get_partner_cabinet")
            and hasattr(PartnerCabinetV1, "approve_payout"),
            "detail": "cabinet+payout",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.partner_cabinet_v1 import PARTNER_CABINET_ROLE_DISPLAY

        expected = {"Insurance", "Leasing", "Banks", "Logistics", "Legal", "Dealers", "Service stations"}
        checks["roles"] = {
            "ok": expected.issubset(set(PARTNER_CABINET_ROLE_DISPLAY.values())),
            "detail": f"{len(PARTNER_CABINET_ROLE_DISPLAY)} roles",
        }
    except Exception as exc:
        checks["roles"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_partner_cabinet_v1 import PartnerCabinetV1

        sample = {
            "partner_name": "SG TAS",
            "partner_code": "sgtas",
            "cabinet_role": "insurance",
            "commission_rate": 0.30,
            "received_leads": 5,
            "active_deals": 2,
            "completed_deals": 3,
            "accrued_commissions": 100,
            "pending_commissions": 40,
            "paid_commissions": 60,
            "recent_deals": [],
        }
        text = PartnerCabinetV1.format_partner_cabinet(sample)
        checks["format"] = {
            "ok": "Partner Cabinet" in text and "Insurance" in text,
            "detail": "cabinet text",
        }
    except Exception as exc:
        checks["format"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_partner_cabinet_tests() -> dict:
    return run_partner_cabinet_test_suite()

# Universal Lead Engine v1 self-test.

from __future__ import annotations

from services.start_payload_parser import parse_start_payload


def run_lead_engine_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.lead_engine import LeadEngineLead, LeadEngineStatus

        checks["model"] = {
            "ok": LeadEngineLead.__tablename__ == "lead_engine_v1_leads",
            "detail": LeadEngineLead.__tablename__,
        }
        checks["statuses"] = {
            "ok": LeadEngineStatus.WON.value == "WON",
            "detail": LeadEngineStatus.WON.value,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_lead_engine import LeadEngineV1

        checks["engine"] = {
            "ok": hasattr(LeadEngineV1, "ingest_from_deep_link")
            and hasattr(LeadEngineV1, "get_admin_dashboard"),
            "detail": "ingest+dashboard",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    payload = parse_start_payload("auto_client utm_source=google utm_campaign=spring ref=PARTNER1")
    checks["utm_parser"] = {
        "ok": (
            payload.link_code == "auto_client"
            and payload.utm_source == "google"
            and payload.utm_campaign == "spring"
            and payload.referral_code == "PARTNER1"
        ),
        "detail": f"{payload.link_code}/{payload.utm_source}",
    }

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_lead_engine_tests() -> dict:
    return run_lead_engine_test_suite()

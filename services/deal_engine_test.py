# Universal Deal Engine v1 self-test.

from __future__ import annotations


def run_deal_engine_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.deal_engine_v1 import DealEngineV1Deal, DealEngineV1Status

        checks["model"] = {
            "ok": DealEngineV1Deal.__tablename__ == "deal_engine_v1_deals",
            "detail": DealEngineV1Deal.__tablename__,
        }
        checks["statuses"] = {
            "ok": DealEngineV1Status.COMPLETED.value == "COMPLETED",
            "detail": DealEngineV1Status.COMPLETED.value,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_deal_engine_v1 import DealEngineV1

        checks["engine"] = {
            "ok": hasattr(DealEngineV1, "create_from_lead")
            and hasattr(DealEngineV1, "get_owner_dashboard"),
            "detail": "convert+dashboard",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.deal_engine_v1 import DEAL_ENGINE_V1_SUPPORTED_VERTICALS

        checks["verticals"] = {
            "ok": {"auto", "agro"}.issubset(DEAL_ENGINE_V1_SUPPORTED_VERTICALS),
            "detail": ",".join(sorted(DEAL_ENGINE_V1_SUPPORTED_VERTICALS)),
        }
    except Exception as exc:
        checks["verticals"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_deal_engine_tests() -> dict:
    return run_deal_engine_test_suite()

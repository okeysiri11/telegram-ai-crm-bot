# SLA Tracking v1 self-test.

from __future__ import annotations


def run_sla_tracking_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_sla_tracking_v1 import SlaTrackingV1

        checks["engine"] = {
            "ok": hasattr(SlaTrackingV1, "get_owner_metrics")
            and hasattr(SlaTrackingV1, "on_lead_created"),
            "detail": "metrics+hooks",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_sla_tracking_v1 import SlaTrackingV1

        checks["traffic"] = {
            "ok": SlaTrackingV1.traffic_light_emoji(10) == "🟢"
            and SlaTrackingV1.traffic_light_emoji(30) == "🟡"
            and SlaTrackingV1.traffic_light_emoji(90) == "🔴",
            "detail": "green/yellow/red",
        }
    except Exception as exc:
        checks["traffic"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.sla_tracking_v1 import SLA_GREEN_MAX_MINUTES, SLA_YELLOW_MAX_MINUTES

        checks["thresholds"] = {
            "ok": SLA_GREEN_MAX_MINUTES == 15 and SLA_YELLOW_MAX_MINUTES == 60,
            "detail": "15/60 min",
        }
    except Exception as exc:
        checks["thresholds"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_sla_tracking_tests() -> dict:
    return run_sla_tracking_test_suite()

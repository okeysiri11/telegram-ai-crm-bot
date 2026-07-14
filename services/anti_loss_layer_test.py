# Anti Loss Layer v1 self-test.

from __future__ import annotations


def run_anti_loss_layer_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_anti_loss_layer_v1 import AntiLossLayerV1

        checks["engine"] = {
            "ok": hasattr(AntiLossLayerV1, "check_lead_duplicate")
            and hasattr(AntiLossLayerV1, "merge_leads"),
            "detail": "check+merge",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_anti_loss_layer_v1 import AntiLossLayerV1

        checks["normalize"] = {
            "ok": AntiLossLayerV1.normalize_phone("+380 67 123-45-67") == "380671234567"
            and AntiLossLayerV1.normalize_vin("abc-123") == "ABC123",
            "detail": "phone+vin",
        }
    except Exception as exc:
        checks["normalize"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_anti_loss_layer_v1 import AntiLossLayerV1

        bundle = AntiLossLayerV1.agro_bundle_value("wheat", "100t", "odesa")
        checks["agro_bundle"] = {
            "ok": bundle == "wheat|100t|odesa",
            "detail": bundle,
        }
    except Exception as exc:
        checks["agro_bundle"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_anti_loss_layer_tests() -> dict:
    return run_anti_loss_layer_test_suite()

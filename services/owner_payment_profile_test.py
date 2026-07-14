# Owner Payment Profile v1 self-test.

from __future__ import annotations


def run_owner_payment_profile_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.owner_payment_profile_v1 import OwnerPaymentProfileV1

        checks["model"] = {
            "ok": OwnerPaymentProfileV1.__tablename__ == "owner_payment_profile_v1",
            "detail": OwnerPaymentProfileV1.__tablename__,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_owner_payment_profile_v1 import OwnerPaymentProfileEngineV1

        mask = OwnerPaymentProfileEngineV1._validate_card_mask("**** **** **** 1234")
        checks["card_mask_ok"] = {
            "ok": mask == "**** **** **** 1234",
            "detail": mask,
        }
        rejected = False
        try:
            OwnerPaymentProfileEngineV1._validate_card_mask("5375 4141 0000 0000")
        except Exception:
            rejected = True
        checks["card_mask_reject_full"] = {
            "ok": rejected,
            "detail": "full card rejected",
        }
        profile = {
            "card_holder_name": "Test LLC",
            "card_mask": "**** **** **** 9999",
            "iban": "UA00TEST",
            "usdt_trc20_wallet": "TTEST",
            "usdt_erc20_wallet": "0xTEST",
            "cash_instructions": "Office 1",
            "default_payment_method": "CARD",
            "enabled_methods": ["CARD", "IBAN"],
        }
        text = OwnerPaymentProfileEngineV1.format_owner_profile(profile)
        checks["format"] = {
            "ok": "**** **** **** 9999" in text and "5375" not in text,
            "detail": "masked only",
        }
        kb = OwnerPaymentProfileEngineV1.owner_settings_keyboard(profile)
        checks["keyboard"] = {
            "ok": len(kb.inline_keyboard) >= 4,
            "detail": str(len(kb.inline_keyboard)),
        }
    except Exception as exc:
        checks["card_mask_ok"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_owner_payment_profile_tests() -> dict:
    return run_owner_payment_profile_test_suite()

# Manual Payment Verification Engine v1 self-test.

from __future__ import annotations

from decimal import Decimal


def run_payment_engine_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.payment_engine_v1 import (
            PAYMENT_ENGINE_METHODS,
            PAYMENT_ENGINE_STATUSES,
            PaymentEngineV1Payment,
            PaymentEngineMethod,
            PaymentEngineStatus,
        )

        checks["model"] = {
            "ok": PaymentEngineV1Payment.__tablename__ == "payment_engine_v1_payments",
            "detail": PaymentEngineV1Payment.__tablename__,
        }
        checks["methods"] = {
            "ok": PAYMENT_ENGINE_METHODS == {
                "CARD",
                "IBAN",
                "USDT_TRC20",
                "USDT_ERC20",
                "CASH",
            },
            "detail": str(len(PAYMENT_ENGINE_METHODS)),
        }
        checks["statuses"] = {
            "ok": PaymentEngineStatus.CONFIRMED.value in PAYMENT_ENGINE_STATUSES,
            "detail": PaymentEngineStatus.CONFIRMED.value,
        }
        checks["usdt_split"] = {
            "ok": PaymentEngineMethod.USDT_TRC20.value in PAYMENT_ENGINE_METHODS,
            "detail": PaymentEngineMethod.USDT_TRC20.value,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_payment_engine_v1 import PaymentEngineV1

        from services.pg_owner_payment_profile_v1 import OwnerPaymentProfileEngineV1

        mask = OwnerPaymentProfileEngineV1._validate_card_mask("**** **** **** 1234")
        checks["card_mask"] = {
            "ok": "1234" in mask and "5375" not in mask,
            "detail": mask,
        }
        profile = {
            "card_holder_name": "LLC",
            "card_mask": "**** **** **** 0000",
            "iban": "UA00",
            "usdt_trc20_wallet": "T",
            "usdt_erc20_wallet": "0x",
            "cash_instructions": "Office",
            "default_payment_method": "CARD",
            "enabled_methods": ["CARD", "IBAN", "USDT_TRC20", "USDT_ERC20", "CASH"],
        }
        text = OwnerPaymentProfileEngineV1.format_owner_profile(profile)
        checks["instructions"] = {
            "ok": "Owner Payment Profile" in text,
            "detail": "profile text",
        }
        kb = OwnerPaymentProfileEngineV1.owner_settings_keyboard(profile)
        checks["keyboard"] = {
            "ok": len(kb.inline_keyboard) >= 4,
            "detail": str(len(kb.inline_keyboard)),
        }
        metrics = {
            "pending": 2,
            "confirmed": 10,
            "rejected": 1,
            "pending_list": [
                {
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "amount": "100.00",
                    "currency": "USD",
                    "payment_method": "CARD",
                }
            ],
        }
        text = PaymentEngineV1.format_owner_payment_analytics(metrics)
        checks["analytics"] = {
            "ok": "Pending: 2" in text and "Confirmed: 10" in text,
            "detail": "dashboard",
        }
    except Exception as exc:
        checks["instructions"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_payment_engine_tests() -> dict:
    return run_payment_engine_test_suite()

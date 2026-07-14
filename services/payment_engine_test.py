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

        iban_text = PaymentEngineV1.payment_instructions(
            "IBAN",
            amount=Decimal("100"),
            currency="USD",
        )
        trc_text = PaymentEngineV1.payment_instructions(
            "USDT_TRC20",
            amount=Decimal("50"),
            currency="USD",
        )
        checks["instructions"] = {
            "ok": "IBAN" in iban_text and "TRC20" in trc_text,
            "detail": "iban+trc20",
        }
        kb = PaymentEngineV1.payment_methods_keyboard()
        checks["keyboard"] = {
            "ok": len(kb.inline_keyboard) == 5,
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

# Cart and Payment Engine v1 self-test.

from __future__ import annotations

from decimal import Decimal


def run_cart_engine_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.cart_engine_v1 import CartEngineV1Order, CartPaymentMethod

        checks["model"] = {
            "ok": CartEngineV1Order.__tablename__ == "cart_engine_v1_orders",
            "detail": CartEngineV1Order.__tablename__,
        }
        checks["methods"] = {
            "ok": len(CartPaymentMethod) >= 4,
            "detail": CartPaymentMethod.CARD.value,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_cart_engine_v1 import CartEngineV1
        from services.cart_service_catalog import AUTO_SERVICES

        cart = CartEngineV1.new_cart_session(vertical="auto")
        CartEngineV1.toggle_service(cart, AUTO_SERVICES[0])
        CartEngineV1.toggle_service(cart, AUTO_SERVICES[1])
        total = CartEngineV1.cart_total(cart)
        checks["cart_total"] = {
            "ok": total == Decimal("75"),
            "detail": str(total),
        }
        from services.pg_owner_payment_profile_v1 import OwnerPaymentProfileEngineV1

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
        checks["instructions"] = {
            "ok": "****" in (profile["card_mask"] or ""),
            "detail": "masked card",
        }
        checks["payment_methods"] = {
            "ok": len(OwnerPaymentProfileEngineV1.owner_settings_keyboard(profile).inline_keyboard) >= 4,
            "detail": "profile keyboard",
        }
    except Exception as exc:
        checks["cart_total"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_cart_engine_tests() -> dict:
    return run_cart_engine_test_suite()

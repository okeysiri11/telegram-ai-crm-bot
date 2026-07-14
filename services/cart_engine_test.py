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
        checks["instructions"] = {
            "ok": "IBAN" in CartEngineV1.payment_instructions("IBAN", amount=Decimal("100"), currency="USD"),
            "detail": "iban",
        }
        checks["payment_methods"] = {
            "ok": len(CartEngineV1.payment_methods_keyboard().inline_keyboard) == 5,
            "detail": "5 methods",
        }
    except Exception as exc:
        checks["cart_total"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_cart_engine_tests() -> dict:
    return run_cart_engine_test_suite()

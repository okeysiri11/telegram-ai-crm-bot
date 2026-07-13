# Automotive Telegram UI v2 self-test for System Health Dashboard.

from __future__ import annotations

import inspect


def run_automotive_ui_self_test() -> dict:
    checks: dict[str, dict] = {}
    try:
        from keyboards import (
            AUTO_VERTICAL_HUB_BUTTONS,
            AUTO_VERTICAL_MAIN_BUTTON,
            AUTO_VERTICAL_MENU_BUTTONS,
            auto_billing_plans_inline,
            auto_vertical_hub_menu,
            auto_vertical_menu,
            owner_main_menu,
        )

        hub = auto_vertical_hub_menu()
        menu = auto_vertical_menu()
        main = owner_main_menu(show_automotive=True)
        main_hidden = owner_main_menu(show_automotive=False)
        hub_texts = {btn.text for row in hub.keyboard for btn in row}
        menu_texts = {btn.text for row in menu.keyboard for btn in row}
        main_texts = {btn.text for row in main.keyboard for btn in row}

        checks["automotive_button"] = {
            "ok": AUTO_VERTICAL_MAIN_BUTTON == "🚗 Авто" and AUTO_VERTICAL_MAIN_BUTTON in main_texts,
            "detail": AUTO_VERTICAL_MAIN_BUTTON,
        }
        checks["automotive_hub_items"] = {
            "ok": AUTO_VERTICAL_HUB_BUTTONS.issubset(hub_texts) and "🏦 Credit" in hub_texts,
            "detail": f"{len(hub_texts)} hub items",
        }
        checks["automotive_menu_items"] = {
            "ok": AUTO_VERTICAL_MENU_BUTTONS.issubset(menu_texts | hub_texts),
            "detail": f"{len(menu_texts)} cars items",
        }
        checks["billing_menu"] = {
            "ok": "💳 Тарифы и услуги" in menu_texts,
            "detail": "💳 Тарифы и услуги",
        }
        checks["main_menu_rbac"] = {
            "ok": AUTO_VERTICAL_MAIN_BUTTON not in {
                btn.text for row in main_hidden.keyboard for btn in row
            },
            "detail": "hidden when show_automotive=False",
        }
        checks["billing_inline"] = {
            "ok": bool(auto_billing_plans_inline().inline_keyboard),
            "detail": "plans keyboard",
        }
    except Exception as exc:
        checks["automotive_button"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        import auto_vertical_handlers as avh

        router = avh.auto_vertical_router
        handler_count = len(router.message.handlers) + len(router.callback_query.handlers)
        source = inspect.getsource(avh)
        checks["automotive_handlers"] = {
            "ok": handler_count >= 5 and "open_auto_vertical" in source,
            "detail": f"{handler_count} handlers",
        }
        checks["billing_handlers"] = {
            "ok": "auto_billing_callback" in source and "auto_billing_receipt_upload" in source,
            "detail": "billing callback + receipt",
        }
    except Exception as exc:
        checks["automotive_handlers"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.automotive_telegram_access import AUTOMOTIVE_UI_ROLES

        checks["rbac_roles"] = {
            "ok": {"OWNER", "SUPER_MANAGER", "AUTO_MANAGER"}.issubset(AUTOMOTIVE_UI_ROLES),
            "detail": ",".join(sorted(AUTOMOTIVE_UI_ROLES)),
        }
    except Exception as exc:
        checks["rbac_roles"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.commercial_billing_engine import (
            BillingEvent,
            CommercialPayment,
            PaymentReceipt,
            SubscriptionHistory,
        )

        tables = {
            t.__tablename__
            for t in (CommercialPayment, PaymentReceipt, SubscriptionHistory, BillingEvent)
        }
        checks["billing_tables"] = {
            "ok": len(tables) == 4,
            "detail": ",".join(sorted(tables)),
        }
    except Exception as exc:
        checks["billing_tables"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}

"""AUTO Telegram integration boundary — reuse existing ADOS bot, no new architecture.

AUTO 1.4 turns prepared intents into live staff authorization inside the shared bot.
A new Telegram bot is not created.
"""

from __future__ import annotations

from typing import Any

from services.auto_ops.crm_catalog import TELEGRAM_CRM_INTENTS
from services.auto_ops.customs_catalog import TELEGRAM_CUSTOMS_INTENTS
from services.auto_ops.logistics_catalog import TELEGRAM_INTENTS
from services.auto_ops.telegram_auth import TELEGRAM_LIVE_INTENTS


def telegram_boundary() -> dict[str, Any]:
    """Honest reuse map for the existing ADOS Telegram stack."""
    return {
        "sprint": "AUTO_1.8.5",
        "status": "live",
        "implemented": True,
        "message_ru": (
            "Команды Авто включены в существующем боте ADOS. "
            "Новый бот не строится. Доступ только у авторизованных сотрудников компании."
        ),
        "reuse": {
            "access": "services/auto_ops/telegram_auth.py + telegram members",
            "roles": "auto_director / auto_accountant / auto_manager / auto_admin",
            "routers": [
                "routers/auto_ops_telegram_router.py",
                "routers/auto_hub_router.py",
                "routers/auto_add_vehicle_router.py",
                "routers/auto_client_router.py",
                "routers/auto_dealer_router.py",
                "auto_vertical_handlers.py",
            ],
            "startup": "startup.py::BOT_ROUTER_PATHS",
            "entrypoint": "main.py",
            "policy": "private authorized users only — never a public VIN/search bot",
        },
        "intents": TELEGRAM_INTENTS + TELEGRAM_CUSTOMS_INTENTS + TELEGRAM_CRM_INTENTS + TELEGRAM_LIVE_INTENTS,
        "constraints": [
            "authorized company users only",
            "no public VIN database",
            "no public client/finance data",
            "reuse existing Telegram bot process",
            "tenant isolation by organization membership",
            "alerts reuse member enabled flag; quiet hours were not in AUTO 1.4",
        ],
    }

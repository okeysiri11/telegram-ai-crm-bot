"""Explicit tracking delivery adapters.

Core destination is recruiting_db (Postgres). External ads/messaging providers
are not called this sprint — they are classified provider_not_configured.
"""

from __future__ import annotations

from typing import Any

CORE_DESTINATIONS = {"", "recruiting_db", "postgres", "recruiting"}
PROVIDER_DESTINATIONS = {"meta", "google", "tiktok", "telegram", "whatsapp", "email"}
TEST_DESTINATIONS = {"test", "dev_test"}


def destination_of(event: dict[str, Any]) -> str:
    raw = str(event.get("destination") or event.get("provider") or "recruiting_db").strip().lower()
    return raw or "recruiting_db"


def is_core_destination(dest: str) -> bool:
    return dest in CORE_DESTINATIONS


def deliver_via_test_adapter(event: dict[str, Any]) -> dict[str, Any]:
    out = dict(event)
    out["destination"] = destination_of(event)
    out["delivery_status"] = "DELIVERED"
    out["delivery_class"] = "delivered"
    out["adapter"] = "test"
    out["message_ru"] = "Доставлено тестовым адаптером."
    return out


def classify_unconfigured_provider(event: dict[str, Any]) -> dict[str, Any]:
    out = dict(event)
    dest = destination_of(event)
    out["destination"] = dest
    out["delivery_status"] = "WAITING_PROVIDER"
    out["delivery_class"] = "waiting_provider"
    out["provider_status"] = "NOT_CONFIGURED"
    out["adapter"] = dest
    out["message_ru"] = (
        f"Провайдер {dest} не настроен; событие сохранено и будет повторено после настройки."
    )
    return out

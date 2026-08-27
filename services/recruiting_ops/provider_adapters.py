"""Provider adapters — LIVE boundaries + MOCK implementations for tests.

LIVE adapters never report CONNECTED without a successful live health check.
This sprint does not call Meta/Google/TikTok/WhatsApp/SMTP networks.
MOCK adapters are visibly mode=MOCK and are forbidden in production.
"""

from __future__ import annotations

import os
import time
from typing import Any

from services.recruiting_ops.provider_contract import (
    ADS_CAPABILITIES,
    LIVE_API_NOT_IMPLEMENTED,
    MESSAGING_CAPABILITIES,
    MOCK_ONLY,
    NOT_CONFIGURED,
    ProviderAdapter,
    adapter_result,
    unsupported,
)
from services.recruiting_ops.runtime import is_production_runtime
from services.recruiting_ops.secret_store import credential_presence, get_secret_store


def mock_providers_allowed() -> bool:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    if is_production_runtime():
        return False
    return (os.getenv("RECRUITING_ALLOW_MOCK_PROVIDERS") or "").strip().lower() in {"1", "true", "yes"}


class LiveProviderAdapter(ProviderAdapter):
    mode = "LIVE"
    public_fields: tuple[str, ...] = ()

    def _credentials_ready(self) -> bool:
        return bool(credential_presence(self.provider)["present"])

    def connect(self, **kwargs: Any) -> dict[str, Any]:
        if not self._credentials_ready():
            return adapter_result(
                ok=False,
                error=NOT_CONFIGURED,
                status="NOT_CONFIGURED",
                mode=self.mode,
                message_ru="Учётные данные не заданы. Провайдер не подключен.",
            )
        return adapter_result(
            ok=True,
            status="CONFIGURING",
            mode=self.mode,
            connected=False,
            message_ru="Учётные данные сохранены. Live API ещё не подтверждался.",
        )

    def disconnect(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=True, status="NOT_CONFIGURED", mode=self.mode, connected=False, message_ru="Подключение отключено.")

    def health_check(self, **_kwargs: Any) -> dict[str, Any]:
        started = time.perf_counter()
        if not self._credentials_ready():
            return adapter_result(
                ok=False,
                error=NOT_CONFIGURED,
                status="NOT_CONFIGURED",
                mode=self.mode,
                connected=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                message_ru="Провайдер не настроен.",
            )
        return adapter_result(
            ok=True,
            error=LIVE_API_NOT_IMPLEMENTED,
            status="CONFIGURING",
            mode=self.mode,
            connected=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            message_ru="Секреты есть, live-запрос к провайдеру в этом спринте не выполняется.",
        )

    def refresh_credentials(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(
            ok=False,
            error=LIVE_API_NOT_IMPLEMENTED,
            status="CONFIGURING",
            mode=self.mode,
            message_ru="Обновление токена live API ещё не подключено.",
        )

    def list_accounts(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, items=[], mode=self.mode, message_ru="Нет живых данных.")

    def list_campaigns(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, items=[], mode=self.mode, message_ru="Нет живых данных.")

    def create_campaign(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, mode=self.mode, message_ru="Создание кампании у провайдера недоступно.")

    def update_campaign(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, mode=self.mode, message_ru="Изменение кампании у провайдера недоступно.")

    def pause_campaign(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, mode=self.mode, message_ru="Пауза у провайдера недоступна.")

    def resume_campaign(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, mode=self.mode, message_ru="Возобновление у провайдера недоступно.")

    def fetch_metrics(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, metrics=None, mode=self.mode, message_ru="Нет живых данных.")

    def fetch_leads(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, items=[], mode=self.mode, message_ru="Нет живых данных.")

    def send_message(self, **_kwargs: Any) -> dict[str, Any]:
        return unsupported("send_message", self.provider)


class MetaAdsAdapter(LiveProviderAdapter):
    provider = "meta"
    label = "Meta Ads"
    capabilities = ADS_CAPABILITIES
    public_fields = ("ad_account_id", "page_id", "business_id")


class GoogleAdsAdapter(LiveProviderAdapter):
    provider = "google"
    label = "Google Ads"
    capabilities = ADS_CAPABILITIES
    public_fields = ("customer_id", "manager_id", "client_id")


class TikTokAdsAdapter(LiveProviderAdapter):
    provider = "tiktok"
    label = "TikTok Ads"
    capabilities = ADS_CAPABILITIES
    public_fields = ("advertiser_id",)


class TelegramAdapter(LiveProviderAdapter):
    provider = "telegram"
    label = "Telegram"
    capabilities = MESSAGING_CAPABILITIES
    public_fields = ("bot_username", "target_chat")

    def send_message(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, sent=False, mode=self.mode, message_ru="Отправка в Telegram не подключена.")


class WhatsAppAdapter(LiveProviderAdapter):
    provider = "whatsapp"
    label = "WhatsApp"
    capabilities = MESSAGING_CAPABILITIES
    public_fields = ("phone_number_id", "business_account_id")

    def send_message(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, sent=False, mode=self.mode, message_ru="Отправка в WhatsApp не подключена.")


class EmailAdapter(LiveProviderAdapter):
    provider = "email"
    label = "Email"
    capabilities = MESSAGING_CAPABILITIES
    public_fields = ("smtp_host", "smtp_user", "email_from", "provider_type")

    def send_message(self, **_kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=False, error=LIVE_API_NOT_IMPLEMENTED, sent=False, mode=self.mode, message_ru="Отправка email не подключена.")


class MockProviderAdapter(ProviderAdapter):
    mode = "MOCK"

    def __init__(self, inner: LiveProviderAdapter) -> None:
        self.inner = inner
        self.provider = inner.provider
        self.label = inner.label
        self.capabilities = inner.capabilities
        self.public_fields = inner.public_fields
        self._connected = False
        self._accounts = [{"id": f"mock-{inner.provider}-acct", "name": f"MOCK {inner.label}"}]
        self._campaigns: list[dict[str, Any]] = []

    def connect(self, **_kwargs: Any) -> dict[str, Any]:
        if not mock_providers_allowed():
            return adapter_result(ok=False, error=MOCK_ONLY, mode=self.mode, message_ru="Mock-режим запрещён в production.")
        self._connected = True
        return adapter_result(
            ok=True,
            status="CONNECTED",
            mode="MOCK",
            connected=True,
            mock=True,
            message_ru="Подключено в режиме MOCK. Это не live-провайдер.",
        )

    def disconnect(self, **_kwargs: Any) -> dict[str, Any]:
        self._connected = False
        return adapter_result(ok=True, status="NOT_CONFIGURED", mode="MOCK", connected=False, mock=True, message_ru="Mock отключён.")

    def health_check(self, **_kwargs: Any) -> dict[str, Any]:
        if not mock_providers_allowed():
            return adapter_result(ok=False, error=MOCK_ONLY, mode=self.mode, message_ru="Mock-режим запрещён в production.")
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, status="NOT_CONFIGURED", mode="MOCK", mock=True, connected=False, message_ru="Mock не подключен.")
        return adapter_result(
            ok=True,
            status="CONNECTED",
            mode="MOCK",
            mock=True,
            connected=True,
            latency_ms=1,
            message_ru="Mock-проверка успешна.",
        )

    def refresh_credentials(self, **_kwargs: Any) -> dict[str, Any]:
        return self.health_check()

    def list_accounts(self, **_kwargs: Any) -> dict[str, Any]:
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, items=[], mode="MOCK")
        return adapter_result(ok=True, items=list(self._accounts), mode="MOCK", mock=True)

    def list_campaigns(self, **_kwargs: Any) -> dict[str, Any]:
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, items=[], mode="MOCK")
        return adapter_result(ok=True, items=list(self._campaigns), mode="MOCK", mock=True)

    def create_campaign(self, **kwargs: Any) -> dict[str, Any]:
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, mode="MOCK")
        item = {"id": f"mock-camp-{len(self._campaigns)+1}", "name": kwargs.get("name") or "MOCK", "status": "ACTIVE", "mock": True}
        self._campaigns.append(item)
        return adapter_result(ok=True, item=item, mode="MOCK", mock=True)

    def update_campaign(self, **kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=True, item={"id": kwargs.get("campaign_id"), "mock": True}, mode="MOCK", mock=True)

    def pause_campaign(self, **kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=True, item={"id": kwargs.get("campaign_id"), "status": "PAUSED", "mock": True}, mode="MOCK", mock=True)

    def resume_campaign(self, **kwargs: Any) -> dict[str, Any]:
        return adapter_result(ok=True, item={"id": kwargs.get("campaign_id"), "status": "ACTIVE", "mock": True}, mode="MOCK", mock=True)

    def fetch_metrics(self, **_kwargs: Any) -> dict[str, Any]:
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, metrics=None, mode="MOCK")
        return adapter_result(ok=True, metrics=None, live=False, mock=True, mode="MOCK", message_ru="Нет живых данных.")

    def fetch_leads(self, **kwargs: Any) -> dict[str, Any]:
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, items=[], mode="MOCK")
        seeded = kwargs.get("items") or []
        return adapter_result(ok=True, items=list(seeded), mode="MOCK", mock=True)

    def send_message(self, **kwargs: Any) -> dict[str, Any]:
        if "send_message" not in self.capabilities:
            return unsupported("send_message", self.provider)
        if not self._connected:
            return adapter_result(ok=False, error=NOT_CONFIGURED, sent=False, mode="MOCK")
        return adapter_result(ok=True, sent=True, mock=True, mode="MOCK", message_ru="Сообщение записано mock-адаптером, live-отправки нет.")


LIVE_ADAPTERS: dict[str, LiveProviderAdapter] = {
    "meta": MetaAdsAdapter(),
    "google": GoogleAdsAdapter(),
    "tiktok": TikTokAdsAdapter(),
    "telegram": TelegramAdapter(),
    "whatsapp": WhatsAppAdapter(),
    "email": EmailAdapter(),
}

_MOCKS: dict[str, MockProviderAdapter] = {}


def get_adapter(provider: str, *, mode: str | None = None) -> ProviderAdapter:
    key = (provider or "").strip().lower()
    live = LIVE_ADAPTERS.get(key)
    if live is None:
        raise KeyError(key)
    requested = (mode or "").upper()
    if requested == "MOCK" or (requested != "LIVE" and mock_providers_allowed() and os.getenv("RECRUITING_PROVIDER_MODE", "").lower() == "mock"):
        mock = _MOCKS.get(key)
        if mock is None:
            mock = MockProviderAdapter(live)
            _MOCKS[key] = mock
        return mock
    return live


def reset_adapters_for_tests() -> None:
    _MOCKS.clear()
    get_secret_store()  # ensure store exists
    from services.recruiting_ops.secret_store import reset_secret_store_for_tests

    reset_secret_store_for_tests()

# Legacy subsystem interfaces — platform knows only these contracts.

from __future__ import annotations

import abc
from typing import Any
from uuid import UUID


class LegacyCRM(abc.ABC):
    @abc.abstractmethod
    async def submit_auto_request(self, **kwargs: Any) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def get_auto_request_summary(self, request_number: str) -> dict[str, Any] | None: ...

    @abc.abstractmethod
    async def list_new_auto_requests(self, *, limit: int = 10) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    async def ingest_lead_from_deep_link(self, **kwargs: Any) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def record_vin_intake(
        self, *, vin: str, car_id: UUID, created_by: int
    ) -> None: ...

    @abc.abstractmethod
    async def get_default_tenant_id(self) -> UUID | None: ...


class LegacyTelegram(abc.ABC):
    @abc.abstractmethod
    def register_bot_routers(self, dispatcher: Any) -> None: ...


class LegacyUserStorage(abc.ABC):
    @abc.abstractmethod
    async def user_has_permission(self, telegram_id: int, permission_code: str) -> bool: ...

    @abc.abstractmethod
    async def ensure_permissions_seeded(self) -> dict[str, Any]: ...


class LegacyNotificationGateway(abc.ABC):
    @abc.abstractmethod
    async def send_to_manager(
        self,
        *,
        manager_telegram_id: int,
        text: str,
        request_number: str | None = None,
    ) -> None: ...

    @abc.abstractmethod
    async def startup_diagnostics(self) -> dict[str, Any]: ...


class LegacyAI(abc.ABC):
    @abc.abstractmethod
    async def ask(self, prompt: str, **kwargs: Any) -> str: ...


class LegacyScheduler(abc.ABC):
    @abc.abstractmethod
    def get_default_worker(self) -> Any: ...


class LegacyAudit(abc.ABC):
    @abc.abstractmethod
    async def log(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: int | None,
        payload: dict[str, Any],
    ) -> str | None: ...


class LegacyWorkflowRules(abc.ABC):
    @abc.abstractmethod
    def register_trigger(
        self,
        trigger_code: str,
        action_type: str,
        module: str = "system",
        action_payload: str | None = None,
    ) -> int: ...

    @abc.abstractmethod
    def fetch_rules(self, trigger_code: str) -> list[tuple[Any, ...]]: ...

    @abc.abstractmethod
    def log_execution(
        self,
        trigger_code: str,
        user_id: int,
        module: str,
        action_type: str,
        *,
        entity_type: str | None = None,
        entity_id: int | None = None,
        status: str = "OK",
        details: str | None = None,
    ) -> int: ...


class LegacyAnalytics(abc.ABC):
    @abc.abstractmethod
    async def owner_dashboard_metrics(self) -> dict[str, Any]: ...

# Dependency Injection container — architecture scaffold.

"""Registers factories for repositories, services, notifications, and storage.

This module does NOT replace legacy wiring. Legacy code continues to import
services directly. Future migration can gradually resolve deps via ``get_container()``.

Usage (future):
    from container import get_container
    storage = get_container().storage()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ServiceRegistry:
    """Simple factory registry (scaffold DI)."""

    _factories: dict[str, Callable[[], Any]] = field(default_factory=dict)
    _singletons: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, factory: Callable[[], Any], *, singleton: bool = True) -> None:
        self._factories[name] = factory
        if not singleton and name in self._singletons:
            self._singletons.pop(name, None)

    def resolve(self, name: str) -> Any:
        if name in self._singletons:
            return self._singletons[name]
        if name not in self._factories:
            raise KeyError(f"Service not registered: {name}")
        instance = self._factories[name]()
        self._singletons[name] = instance
        return instance

    def registered_names(self) -> list[str]:
        return sorted(self._factories)


class AppContainer:
    """Application container — scaffold only; not wired into bot startup."""

    def __init__(self) -> None:
        self.registry = ServiceRegistry()
        self._bootstrap()

    def _bootstrap(self) -> None:
        # Storage
        self.registry.register("storage", _build_storage)
        self.registry.register("storage.telegram", lambda: _import_telegram_storage())
        self.registry.register("storage.local", lambda: _import_local_storage())
        self.registry.register("storage.s3", lambda: _import_s3_storage())

        # Notifications
        self.registry.register("notifications", _build_notification_center)
        self.registry.register("notifications.telegram", lambda: _import_telegram_notifier())
        self.registry.register("notifications.email", lambda: _import_email_notifier())
        self.registry.register("notifications.sms", lambda: _import_sms_notifier())
        self.registry.register("notifications.push", lambda: _import_push_notifier())

        # Domain service placeholders (lazy imports — legacy engines)
        self.registry.register(
            "services.client_request_crm",
            lambda: _lazy("services.pg_client_request_crm_engine", "ClientRequestCrmEngineV1"),
        )
        self.registry.register(
            "services.inventory",
            lambda: _lazy("services.pg_marketplace_inventory_engine", "InventoryEngineV1"),
        )
        self.registry.register(
            "services.ai_manager",
            lambda: _lazy("services.pg_ai_manager_engine", "AiManagerEngineV1"),
        )
        self.registry.register(
            "services.platform_audit",
            lambda: _lazy("services.pg_platform_audit_engine", "PlatformAuditEngineV1"),
        )

        # Repository placeholders (point at existing repository modules when available)
        self.registry.register(
            "repositories.client_request",
            lambda: _lazy("repositories.client_request_repository", "ClientRequestRepository"),
        )
        self.registry.register(
            "repositories.auto_client_request",
            lambda: _lazy(
                "repositories.auto_client_request_repository",
                "AutoClientRequestRepository",
            ),
        )

        # Vertical services (strangler layer)
        for code in ("auto", "agro", "realty", "legal", "logistics"):
            self.registry.register(
                f"verticals.{code}",
                lambda c=code: _lazy(f"src.verticals.{c}.service", f"{c.title()}VerticalService"),
            )

    def vertical(self, code: str) -> Any:
        return self.registry.resolve(f"verticals.{code}")

    def storage(self) -> Any:
        return self.registry.resolve("storage")

    def notifications(self) -> Any:
        return self.registry.resolve("notifications")

    def get(self, name: str) -> Any:
        return self.registry.resolve(name)


_CONTAINER: AppContainer | None = None


def get_container() -> AppContainer:
    global _CONTAINER
    if _CONTAINER is None:
        _CONTAINER = AppContainer()
    return _CONTAINER


def reset_container() -> None:
    """Test helper — clears singleton container."""
    global _CONTAINER
    _CONTAINER = None


def _lazy(module: str, attr: str) -> Any:
    import importlib

    mod = importlib.import_module(module)
    return getattr(mod, attr)


def _build_storage() -> Any:
    from src.platform.storage import get_storage_provider

    return get_storage_provider()


def _build_notification_center() -> Any:
    from src.platform.notifications import NotificationCenter

    return NotificationCenter()


def _import_telegram_storage() -> Any:
    from src.platform.storage import TelegramStorage

    return TelegramStorage()


def _import_local_storage() -> Any:
    from src.platform.storage import LocalStorage

    return LocalStorage()


def _import_s3_storage() -> Any:
    from src.platform.storage import S3Storage

    return S3Storage()


def _import_telegram_notifier() -> Any:
    from src.platform.notifications import TelegramProvider

    return TelegramProvider()


def _import_email_notifier() -> Any:
    from src.platform.notifications import EmailProvider

    return EmailProvider()


def _import_sms_notifier() -> Any:
    from src.platform.notifications import SMSProvider

    return SMSProvider()


def _import_push_notifier() -> Any:
    from src.platform.notifications import PushProvider

    return PushProvider()

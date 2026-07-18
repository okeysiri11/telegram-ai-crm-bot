# PlatformVertical — abstract base for extensible business verticals.

from __future__ import annotations

import logging
import uuid
from abc import ABC
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

from platform_sdk.platform_context import PlatformContext

logger = logging.getLogger(__name__)


@dataclass
class SlaPolicy:
    assignment_sec: int = 900
    first_response_sec: int = 1800
    close_sec: int = 259200


@dataclass
class NotificationPolicy:
    notify_on_create: bool = True
    notify_on_assign: bool = True
    notify_on_complete: bool = True
    notify_on_overdue: bool = True
    notify_owner_on_escalation: bool = True


@dataclass
class ValidationPolicy:
    required_fields: list[str] = field(default_factory=lambda: ["client_telegram_id"])
    require_vin: bool = False
    require_phone: bool = False


class PlatformVertical(ABC):
    """Every business vertical implements this contract."""

    vertical_code: ClassVar[str]
    workflow_name: ClassVar[str]
    manager_strategy: ClassVar[str] = "SMART"

    sla_policy: ClassVar[SlaPolicy] = SlaPolicy()
    notification_policy: ClassVar[NotificationPolicy] = NotificationPolicy()
    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy()

    _ctx: PlatformContext | None = None

    @property
    def context(self) -> PlatformContext:
        if self._ctx is None:
            raise RuntimeError(f"Vertical {self.vertical_code} is not built — call build() first")
        return self._ctx

    def register(self) -> None:
        """Register this vertical class with the global registry."""
        from platform_sdk.vertical_registry import vertical_registry

        vertical_registry.register(self.__class__)

    @classmethod
    def build(cls, ctx: PlatformContext) -> PlatformVertical:
        """Wire providers and load workflow — called by VerticalBuilder."""
        instance = cls()
        instance._ctx = ctx
        ctx.workflows.ensure_loaded()
        try:
            ctx.workflows.get_definition(cls.workflow_name)
        except Exception:
            # Fallback: vertical post-create workflow by vertical code
            if ctx.workflows.get_for_vertical(cls.vertical_code.upper()) is None:
                logger.debug(
                    "workflow_not_preloaded vertical=%s name=%s",
                    cls.vertical_code,
                    cls.workflow_name,
                )
        logger.info("vertical_built code=%s workflow=%s", cls.vertical_code, cls.workflow_name)
        return instance

    async def create_request(self, **kwargs: Any) -> dict[str, Any]:
        """Create a request using SDK providers (default CRM flow)."""
        ctx = self.context
        ctx.validation.validate_policy(kwargs, asdict(self.validation_policy))

        manager = await self.assign_manager(request=kwargs)
        manager_uuid = uuid.UUID(manager["user_id"]) if manager and manager.get("user_id") else None

        from services.request_service import RequestService
        from services.system_roles import normalize_vertical

        key = normalize_vertical(self.vertical_code) or self.vertical_code
        request_type = kwargs.get("request_type") or f"{key.upper()}_REQUEST"

        result = await RequestService.persist_crm_request(
            vertical_code=self.vertical_code,
            client_telegram_id=int(kwargs["client_telegram_id"]),
            client_username=kwargs.get("client_username"),
            client_name=kwargs.get("client_name"),
            client_first_name=kwargs.get("client_first_name"),
            description=kwargs.get("description"),
            product=kwargs.get("product"),
            request_type=request_type,
            manager_uuid=manager_uuid,
        )
        await ctx.events.publish_request_created(
            request_id=str(result["id"]),
            request_number=result["request_number"],
            vertical=key,
            request_type=request_type,
            client_telegram_id=result.get("client_telegram_id"),
            client_name=str(kwargs.get("client_name") or ""),
            manager_id=result.get("manager_id"),
            manager_telegram_id=int(manager["telegram_id"]) if manager and manager.get("telegram_id") else None,
        )

        if self.notification_policy.notify_on_create:
            await ctx.notifications.notify_created(
                vertical=key,
                request_number=result["request_number"],
                client_name=str(kwargs.get("client_name") or ""),
                product=str(kwargs.get("product") or kwargs.get("description") or ""),
                manager_telegram_id=int(manager["telegram_id"]) if manager and manager.get("telegram_id") else None,
            )

        await ctx.workflows.run_post_create(
            vertical_code=self.vertical_code,
            workflow_name=self.workflow_name,
            telegram_user={
                "id": kwargs["client_telegram_id"],
                "name": kwargs.get("client_name") or "",
                "username": kwargs.get("client_username"),
            },
            request=result,
            manager=manager,
            variables={"description": kwargs.get("description") or kwargs.get("product") or ""},
        )
        return result

    async def assign_manager(
        self,
        *,
        request: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        ctx = self.context
        payload = dict(request or kwargs)
        return await ctx.manager.resolve_manager(
            self.vertical_code,
            payload,
            strategy=self.manager_strategy,
        )

    async def complete_request(self, request_id: str, **kwargs: Any) -> dict[str, Any] | None:
        from services.request_service import RequestService

        result = await RequestService.complete_request(request_id)
        if result and self.notification_policy.notify_on_complete:
            await self.context.notifications.notify_completed(
                request_number=str(result.get("request_number") or ""),
                client_telegram_id=result.get("client_telegram_id"),
                bot=kwargs.get("bot"),
            )
        return result

    @staticmethod
    def _snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "request_number": row.request_number,
            "request_type": row.request_type,
            "status": row.status,
            "vertical": (row.request_type or "").split("_")[0].lower(),
            "client_telegram_id": row.client_telegram_id,
            "client_name": row.client_first_name or row.client_username,
            "description": row.description,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @classmethod
    def vertical_metadata(cls) -> dict[str, Any]:
        return {
            "code": cls.vertical_code,
            "workflow_name": cls.workflow_name,
            "manager_strategy": cls.manager_strategy,
        }

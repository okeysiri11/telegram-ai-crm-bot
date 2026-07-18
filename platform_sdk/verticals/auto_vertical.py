# AUTO vertical — interactive buy/sell flow + smart assignment.

from __future__ import annotations

from typing import Any, ClassVar

from config import SLA_ASSIGNMENT_SEC, SLA_CLOSE_SEC, SLA_FIRST_RESPONSE_SEC
from platform_sdk.base_vertical import (
    NotificationPolicy,
    PlatformVertical,
    SlaPolicy,
    ValidationPolicy,
)


class AutoVertical(PlatformVertical):
    vertical_code: ClassVar[str] = "auto"
    workflow_name: ClassVar[str] = "auto_buy"
    manager_strategy: ClassVar[str] = "SMART"

    sla_policy: ClassVar[SlaPolicy] = SlaPolicy(
        assignment_sec=SLA_ASSIGNMENT_SEC,
        first_response_sec=SLA_FIRST_RESPONSE_SEC,
        close_sec=SLA_CLOSE_SEC,
    )
    notification_policy: ClassVar[NotificationPolicy] = NotificationPolicy(
        notify_on_create=True,
        notify_on_assign=True,
    )
    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy(
        required_fields=["client_telegram_id"],
        require_vin=False,
        require_phone=False,
    )

    async def create_request(self, **kwargs: Any) -> dict[str, Any]:
        ctx = self.context
        ctx.validation.validate_policy(kwargs, {
            "required_fields": self.validation_policy.required_fields,
            "require_vin": self.validation_policy.require_vin,
            "require_phone": self.validation_policy.require_phone,
        })
        if kwargs.get("vin"):
            ctx.validation.validate_vin(str(kwargs["vin"]))

        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await AutoClientRequestEngineV1.submit(
            client_telegram_id=int(kwargs["client_telegram_id"]),
            client_username=kwargs.get("client_username"),
            client_full_name=kwargs.get("client_name") or kwargs.get("client_full_name") or "",
            flow_request_type=kwargs.get("request_type") or kwargs.get("flow_request_type") or "buy_car",
            description=kwargs.get("description") or kwargs.get("product") or "",
            **{k: v for k, v in kwargs.items() if k not in {"client_name", "request_type"}},
        )

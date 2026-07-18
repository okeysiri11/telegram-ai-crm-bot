# AUTO vertical — interactive buy/sell flow + smart assignment.

from __future__ import annotations

from typing import Any, ClassVar

from platform_configuration.config_provider import config_provider
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

    @classmethod
    def _current_sla(cls) -> SlaPolicy:
        sla = config_provider.sla_settings()
        return SlaPolicy(
            assignment_sec=sla["assignment_sec"],
            first_response_sec=sla["first_response_sec"],
            close_sec=sla["close_sec"],
        )

    sla_policy: ClassVar[SlaPolicy] = SlaPolicy()
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

        from platform_legacy import legacy

        return await legacy.crm.submit_auto_request(
            client_telegram_id=int(kwargs["client_telegram_id"]),
            client_username=kwargs.get("client_username"),
            client_full_name=kwargs.get("client_name") or kwargs.get("client_full_name") or "",
            flow_request_type=kwargs.get("request_type") or kwargs.get("flow_request_type") or "buy_car",
            description=kwargs.get("description") or kwargs.get("product") or "",
            **{k: v for k, v in kwargs.items() if k not in {"client_name", "request_type"}},
        )

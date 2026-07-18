# REALTY vertical.

from __future__ import annotations

from typing import ClassVar

from platform_sdk.base_vertical import NotificationPolicy, PlatformVertical, ValidationPolicy


class RealtyVertical(PlatformVertical):
    vertical_code: ClassVar[str] = "realty"
    workflow_name: ClassVar[str] = "realty_post_create"
    manager_strategy: ClassVar[str] = "SMART"

    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy(
        required_fields=["client_telegram_id"],
        require_phone=False,
    )
    notification_policy: ClassVar[NotificationPolicy] = NotificationPolicy(
        notify_on_create=True,
    )

# AGRO vertical.

from __future__ import annotations

from typing import ClassVar

from platform_sdk.base_vertical import NotificationPolicy, PlatformVertical, ValidationPolicy


class AgroVertical(PlatformVertical):
    vertical_code: ClassVar[str] = "agro"
    workflow_name: ClassVar[str] = "agro_post_create"
    manager_strategy: ClassVar[str] = "SMART"

    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy(
        required_fields=["client_telegram_id", "description"],
    )
    notification_policy: ClassVar[NotificationPolicy] = NotificationPolicy(
        notify_on_create=True,
    )

# LOGISTICS vertical.

from __future__ import annotations

from typing import ClassVar

from platform_sdk.base_vertical import PlatformVertical, ValidationPolicy


class LogisticsVertical(PlatformVertical):
    vertical_code: ClassVar[str] = "logistics"
    workflow_name: ClassVar[str] = "logistics_post_create"
    manager_strategy: ClassVar[str] = "SMART"

    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy(
        required_fields=["client_telegram_id", "description"],
    )

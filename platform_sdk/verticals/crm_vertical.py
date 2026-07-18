# CRM vertical — generic CRM requests.

from __future__ import annotations

from typing import ClassVar

from platform_sdk.base_vertical import PlatformVertical, ValidationPolicy


class CrmVertical(PlatformVertical):
    vertical_code: ClassVar[str] = "crm"
    workflow_name: ClassVar[str] = "crm_post_create"
    manager_strategy: ClassVar[str] = "SMART"

    validation_policy: ClassVar[ValidationPolicy] = ValidationPolicy(
        required_fields=["client_telegram_id"],
    )

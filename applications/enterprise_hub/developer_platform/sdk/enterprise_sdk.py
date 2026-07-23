"""Unified Enterprise SDK facade for plugin authors."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.developer_platform.sdk.ai_sdk import AiSdk
from applications.enterprise_hub.developer_platform.sdk.crm_sdk import CrmSdk
from applications.enterprise_hub.developer_platform.sdk.event_sdk import EventSdk
from applications.enterprise_hub.developer_platform.sdk.integration_sdk import IntegrationSdk
from applications.enterprise_hub.developer_platform.sdk.security_sdk import SecuritySdk
from applications.enterprise_hub.developer_platform.sdk.ui_sdk import UiSdk
from applications.enterprise_hub.developer_platform.sdk.workflow_sdk import WorkflowSdk
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class EnterpriseSdk:
    """Unified SDK facade (CRM/ERP/Workflow/AI/Events/UI/Integrations/Security/Knowledge)."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.crm = CrmSdk(self.store)
        self.workflow = WorkflowSdk(self.store)
        self.ai = AiSdk(self.store)
        self.events = EventSdk(self.store)
        self.ui = UiSdk(self.store)
        self.integrations = IntegrationSdk(self.store)
        self.security = SecuritySdk(self.store)

    def describe(self) -> dict[str, Any]:
        return {
            "sdk": "enterprise",
            "surfaces": [
                "crm",
                "erp",
                "workflow",
                "ai",
                "events",
                "knowledge",
                "security",
                "integrations",
                "ui",
            ],
            "version": "1.0",
            "crm": self.crm.capabilities(),
            "workflow": self.workflow.capabilities(),
            "ai": self.ai.capabilities(),
            "events": self.events.capabilities(),
            "ui": self.ui.capabilities(),
            "integrations": self.integrations.capabilities(),
            "security": self.security.capabilities(),
        }

    def call(
        self,
        *,
        surface: str,
        method: str,
        plugin_id: str = "system",
        payload: dict | None = None,
    ) -> dict[str, Any]:
        mapping = {
            "crm": self.crm,
            "erp": self.crm,
            "workflow": self.workflow,
            "ai": self.ai,
            "events": self.events,
            "ui": self.ui,
            "integrations": self.integrations,
            "security": self.security,
            "knowledge": self.ai,
        }
        sdk = mapping.get(surface)
        if not sdk:
            raise ValidationError(f"unknown SDK surface: {surface}")
        return sdk.invoke(method=method, plugin_id=plugin_id, payload=payload or {})

    def status(self) -> dict[str, Any]:
        return {"calls": len(self.store.sdp_sdk_calls.list_all()), "surfaces": 9}

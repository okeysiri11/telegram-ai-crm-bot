# PortERPApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.port_erp.billing.service import BillingService, billing_service
from applications.port_erp.config import DEFAULT_CONFIG, PortERPConfig
from applications.port_erp.customs.facade import CustomsDomainEngine, customs_domain_engine
from applications.port_erp.digital_twin.facade import AIOperationsDomainEngine, ai_operations_domain_engine
from applications.port_erp.documents.service import DocumentsService, documents_service
from applications.port_erp.finance.facade import FinanceDomainEngine, finance_domain_engine
from applications.port_erp.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.multimodal.facade import LogisticsDomainEngine, logistics_domain_engine
from applications.port_erp.operations.live import LivePortOperations, live_port_operations
from applications.port_erp.port_core.engine import PortCoreEngine, port_core
from applications.port_erp.security.permissions import PermissionService, permission_service
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.engine import (
    TerminalOperationsEngine,
    terminal_operations_engine,
)
from applications.port_erp.tracking.engine import LiveTrackingEngine, live_tracking_engine


class PortERPApplication:
    """Port ERP — Platform Core v3 + Ecosystem v1.5 via bridges only."""

    def __init__(
        self,
        *,
        config: PortERPConfig | None = None,
        store: PortStore | None = None,
        core: PortCoreEngine | None = None,
        documents: DocumentsService | None = None,
        billing: BillingService | None = None,
        permissions: PermissionService | None = None,
        tracking: LiveTrackingEngine | None = None,
        terminal: TerminalOperationsEngine | None = None,
        customs: CustomsDomainEngine | None = None,
        logistics: LogisticsDomainEngine | None = None,
        ai_ops: AIOperationsDomainEngine | None = None,
        finance: FinanceDomainEngine | None = None,
        live_operations: LivePortOperations | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or port_store
        self.core = core or port_core
        self.documents = documents or documents_service
        self.billing = billing or billing_service
        self.permissions = permissions or permission_service
        self.tracking = tracking or live_tracking_engine
        self.terminal = terminal or terminal_operations_engine
        self.customs = customs or customs_domain_engine
        self.logistics = logistics or logistics_domain_engine
        self.ai_ops = ai_ops or ai_operations_domain_engine
        self.finance = finance or finance_domain_engine
        self.live_operations = live_operations or live_port_operations
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()
        self.ai_ops.twin.set_weather(condition="clear")

    def health(self) -> dict[str, Any]:
        return {
            "application": "port_erp",
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_version": self.config.api_version,
            "port_core": self.config.port_core,
            "tracking_engine": self.config.tracking_engine,
            "terminal_engine": self.config.terminal_engine,
            "customs_engine": self.config.customs_engine,
            "logistics_engine": self.config.logistics_engine,
            "ai_operations_engine": self.config.ai_operations_engine,
            "finance_engine": self.config.finance_engine,
            "metrics": self.core.metrics(),
            "tracking": self.tracking.metrics(),
            "terminal": self.terminal.metrics(),
            "customs": self.customs.metrics(),
            "logistics": self.logistics.metrics(),
            "ai_ops": self.ai_ops.metrics(),
            "finance": self.finance.metrics(),
            "roles": self.permissions.roles(),
            "platform": self.platform.platform_health(),
            "ecosystem": self.ecosystem.ecosystem_health(),
        }


port_erp = PortERPApplication()

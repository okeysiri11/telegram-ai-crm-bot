# PortCoreEngine — foundation facade for Port ERP registries.

from __future__ import annotations

from typing import Any

from applications.port_erp.berths.service import BerthManager, berth_manager
from applications.port_erp.billing.service import BillingService, billing_service
from applications.port_erp.cargo.service import CargoRegistry, cargo_registry
from applications.port_erp.companies.service import CompanyRegistry, company_registry
from applications.port_erp.containers.service import ContainerRegistry, container_registry
from applications.port_erp.customers.service import CustomerRegistry, customer_registry
from applications.port_erp.documents.service import DocumentsService, documents_service
from applications.port_erp.operations.service import OperationsService, operations_service
from applications.port_erp.port_management.service import PortRegistry, port_registry
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminals.service import TerminalRegistry, terminal_registry
from applications.port_erp.vessels.service import VesselRegistry, vessel_registry


class PortCoreEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        ports: PortRegistry | None = None,
        terminals: TerminalRegistry | None = None,
        berths: BerthManager | None = None,
        vessels: VesselRegistry | None = None,
        containers: ContainerRegistry | None = None,
        cargo: CargoRegistry | None = None,
        customers: CustomerRegistry | None = None,
        companies: CompanyRegistry | None = None,
        operations: OperationsService | None = None,
        documents: DocumentsService | None = None,
        billing: BillingService | None = None,
    ) -> None:
        self._store = store or port_store
        self.ports = ports or port_registry
        self.terminals = terminals or terminal_registry
        self.berths = berths or berth_manager
        self.vessels = vessels or vessel_registry
        self.containers = containers or container_registry
        self.cargo = cargo or cargo_registry
        self.customers = customers or customer_registry
        self.companies = companies or company_registry
        self.operations = operations or operations_service
        self.documents = documents or documents_service
        self.billing = billing or billing_service

    def metrics(self) -> dict[str, Any]:
        return {
            "ports": self._store.ports.count(),
            "terminals": self._store.terminals.count(),
            "berths": self._store.berths.count(),
            "vessels": self._store.vessels.count(),
            "voyages": self._store.voyages.count(),
            "containers": self._store.containers.count(),
            "cargo": self._store.cargo.count(),
            "customers": self._store.customers.count(),
            "companies": {
                "shipping_lines": self._store.shipping_lines.count(),
                "forwarders": self._store.forwarders.count(),
                "brokers": self._store.customs_brokers.count(),
                "carriers": self._store.carriers.count(),
                "operators": self._store.port_operators.count(),
            },
            "operations": self.operations.metrics(),
            "documents": self._store.documents.count(),
            "invoices": self._store.invoices.count(),
        }


port_core = PortCoreEngine()

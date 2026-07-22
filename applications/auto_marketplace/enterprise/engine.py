# Enterprise Integration — ERP/CRM/accounting/gov/insurance/bank/dealer/auction/fleet connectors.

from __future__ import annotations

from applications.auto_marketplace.enterprise.models import ConnectorKind, EnterpriseConnector
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class EnterpriseIntegrationEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, connector: EnterpriseConnector) -> EnterpriseConnector:
        if not connector.name:
            raise ValidationError("name is required")
        connector.status = "registered"
        return self._store.enterprise_connectors.save(connector.connector_id, connector)

    def get(self, connector_id: str) -> EnterpriseConnector:
        item = self._store.enterprise_connectors.get(connector_id)
        if item is None:
            raise NotFoundError("EnterpriseConnector", connector_id)
        return item

    def list_connectors(self, *, kind: str = "") -> list[EnterpriseConnector]:
        items = self._store.enterprise_connectors.list_all()
        if kind:
            items = [c for c in items if c.kind.value == kind]
        return items

    def ping(self, connector_id: str) -> dict:
        connector = self.get(connector_id)
        connector.status = "healthy"
        self._store.enterprise_connectors.save(connector_id, connector)
        return {"connector_id": connector_id, "status": "healthy", "kind": connector.kind.value}

    def bootstrap_defaults(self) -> list[EnterpriseConnector]:
        defaults = [
            ("SAP ERP", ConnectorKind.ERP, "/ext/erp"),
            ("Dealer CRM Sync", ConnectorKind.CRM, "/ext/crm"),
            ("Ledger Accounting", ConnectorKind.ACCOUNTING, "/ext/accounting"),
            ("Gov Vehicle Registry", ConnectorKind.GOVERNMENT, "/ext/gov"),
            ("Insurance Hub", ConnectorKind.INSURANCE, "/ext/insurance"),
            ("Banking Rails", ConnectorKind.BANKING, "/ext/banking"),
            ("Dealer Network API", ConnectorKind.DEALER, "/ext/dealers"),
            ("Auction Feed", ConnectorKind.AUCTION, "/ext/auctions"),
            ("Fleet Ops API", ConnectorKind.FLEET, "/ext/fleet"),
        ]
        out = []
        for name, kind, endpoint in defaults:
            out.append(self.register(EnterpriseConnector(name=name, kind=kind, endpoint=endpoint)))
        return out

    def metrics(self) -> dict:
        return {
            "connectors": self._store.enterprise_connectors.count(),
            "kinds": [k.value for k in ConnectorKind],
        }


enterprise_integration_engine = EnterpriseIntegrationEngine()

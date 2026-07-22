# Enterprise Integration Engine — catalog of enterprise connectors.

from __future__ import annotations

from applications.port_erp.enterprise.models import IntegrationTarget
from applications.port_erp.integration.engine import IntegrationEngine, integration_engine


class EnterpriseIntegrationEngine:
    """High-level enterprise integration surface for Port ERP."""

    CONNECTORS = [t.value for t in IntegrationTarget]

    def __init__(self, integration: IntegrationEngine | None = None) -> None:
        self._integration = integration or integration_engine

    def connectors(self) -> list[str]:
        return list(self.CONNECTORS)

    def bootstrap(self) -> dict:
        created = self._integration.ensure_defaults()
        for link in self._integration.list_links():
            if link.status.value == "registered":
                self._integration.connect(link.link_id)
        return {
            "connectors": self.connectors(),
            "created": len(created),
            "matrix": self._integration.status_matrix(),
        }

    def matrix(self) -> dict[str, str]:
        return self._integration.status_matrix()


enterprise_integration_engine = EnterpriseIntegrationEngine()

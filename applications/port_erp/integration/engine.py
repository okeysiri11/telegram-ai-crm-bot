# Integration Engine — connect Port ERP to enterprise systems via bridges only.

from __future__ import annotations

import time

from applications.port_erp.enterprise.events import IntegrationConnectedEvent
from applications.port_erp.enterprise.models import (
    IntegrationLink,
    IntegrationStatus,
    IntegrationTarget,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class IntegrationEngine:
    """Enterprise integration catalog (Agro, Auto, CRM, ERP, twin, identity, bus)."""

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store
        self._events: list[dict] = []

    def targets(self) -> list[str]:
        return [t.value for t in IntegrationTarget]

    def register(self, link: IntegrationLink) -> IntegrationLink:
        if not link.endpoint and link.target not in (
            IntegrationTarget.DIGITAL_TWIN,
            IntegrationTarget.IDENTITY,
            IntegrationTarget.COMMUNICATION_BUS,
            IntegrationTarget.AI_WORKFORCE,
            IntegrationTarget.KNOWLEDGE_GRAPH,
            IntegrationTarget.FINANCE,
            IntegrationTarget.ACCOUNTING,
            IntegrationTarget.WAREHOUSE,
        ):
            # allow empty endpoint for internal bridge targets
            pass
        return self._store.integration_links.save(link.link_id, link)

    def get(self, link_id: str) -> IntegrationLink:
        link = self._store.integration_links.get(link_id)
        if link is None:
            raise NotFoundError("integration_link", link_id)
        return link

    def list_links(self, target: str | None = None) -> list[IntegrationLink]:
        items = self._store.integration_links.list_all()
        if target:
            items = [i for i in items if i.target.value == target]
        return items

    def connect(self, link_id: str) -> IntegrationLink:
        link = self.get(link_id)
        link.status = IntegrationStatus.CONNECTED
        link.last_ping_at = time.time()
        self._store.integration_links.save(link.link_id, link)
        event = IntegrationConnectedEvent(link_id=link.link_id, target=link.target.value)
        self._events.append(event.to_dict())
        return link

    def ping(self, link_id: str) -> IntegrationLink:
        link = self.get(link_id)
        # Bridge-style ping — mark connected without modifying Platform/Ecosystem.
        link.status = IntegrationStatus.CONNECTED
        link.last_ping_at = time.time()
        return self._store.integration_links.save(link.link_id, link)

    def ensure_defaults(self) -> list[IntegrationLink]:
        existing = {l.target for l in self.list_links()}
        created = []
        defaults = [
            (IntegrationTarget.AGRO_MARKETPLACE, "/api/agro/v1"),
            (IntegrationTarget.AUTO_MARKETPLACE, "/api/auto/v1"),
            (IntegrationTarget.CRM, "internal:crm"),
            (IntegrationTarget.ERP, "internal:erp"),
            (IntegrationTarget.WAREHOUSE, "internal:warehouse"),
            (IntegrationTarget.ACCOUNTING, "internal:accounting"),
            (IntegrationTarget.FINANCE, "internal:finance"),
            (IntegrationTarget.AI_WORKFORCE, "bridge:platform"),
            (IntegrationTarget.DIGITAL_TWIN, "internal:digital_twin"),
            (IntegrationTarget.KNOWLEDGE_GRAPH, "bridge:platform"),
            (IntegrationTarget.IDENTITY, "bridge:ecosystem"),
            (IntegrationTarget.COMMUNICATION_BUS, "bridge:ecosystem"),
        ]
        for target, endpoint in defaults:
            if target in existing:
                continue
            created.append(self.register(IntegrationLink(target=target, endpoint=endpoint)))
        return created

    def status_matrix(self) -> dict[str, str]:
        matrix = {t.value: "missing" for t in IntegrationTarget}
        for link in self.list_links():
            matrix[link.target.value] = link.status.value
        return matrix


integration_engine = IntegrationEngine()

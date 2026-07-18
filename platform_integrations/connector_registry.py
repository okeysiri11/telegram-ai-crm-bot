# Connector instance registry — live connector objects.

from __future__ import annotations

import logging
from typing import Any

from platform_integrations.connector_base import ConnectorBase
from platform_integrations.connector_loader import connector_loader
from platform_integrations.exceptions import ConnectorNotFoundError
from platform_integrations.models import ConnectorMetadata

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorBase] = {}
        self._metadata: dict[str, ConnectorMetadata] = {}

    def register(
        self,
        provider: str,
        *,
        connector_id: str | None = None,
        config: dict[str, Any] | None = None,
        enabled: bool = True,
        description: str = "",
    ) -> ConnectorMetadata:
        cid = connector_id or f"{provider}-default"
        connector = connector_loader.create(provider, cid, config=config)
        self._connectors[cid] = connector

        meta = ConnectorMetadata(
            connector_id=cid,
            provider=provider,
            connector_type=connector.connector_type.value,
            version=connector.version,
            enabled=enabled,
            description=description or f"{provider} connector",
            config=config or {},
        )
        self._metadata[cid] = meta
        logger.info("connector_registered id=%s provider=%s", cid, provider)
        return meta

    def get(self, connector_id: str) -> ConnectorBase:
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise ConnectorNotFoundError(f"Connector {connector_id} not found")
        return connector

    def get_metadata(self, connector_id: str) -> ConnectorMetadata:
        meta = self._metadata.get(connector_id)
        if meta is None:
            raise ConnectorNotFoundError(f"Connector {connector_id} not found")
        return meta

    def list_metadata(self) -> list[ConnectorMetadata]:
        return list(self._metadata.values())

    def enable(self, connector_id: str) -> ConnectorMetadata:
        meta = self.get_metadata(connector_id)
        meta.enabled = True
        return meta

    def disable(self, connector_id: str) -> ConnectorMetadata:
        meta = self.get_metadata(connector_id)
        meta.enabled = False
        return meta

    def reset(self) -> None:
        self._connectors.clear()
        self._metadata.clear()


connector_registry = ConnectorRegistry()

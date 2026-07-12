# Automotive Marketplace connectors — normalized listing fetch layer.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from database.models.automotive_marketplace import ConnectorCredential, ConnectorType


@dataclass
class NormalizedListing:
    external_id: str
    vin: str
    make: str
    model: str
    year: int
    price: Decimal | None = None
    currency: str = "USD"
    mileage: int | None = None
    color: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    images: list[str] = field(default_factory=list)
    location: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class BaseMarketplaceConnector(ABC):
    connector_type: str

    @abstractmethod
    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        raise NotImplementedError


class CopartConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.COPART.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


class IAAIConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.IAAI.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


class AutoRiaConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.AUTORIA.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


class OlxAutoConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.OLX_AUTO.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


class MobileDeConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.MOBILE_DE.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


class LocalDealerConnector(BaseMarketplaceConnector):
    connector_type = ConnectorType.LOCAL_DEALER.value

    async def fetch_listings(
        self,
        credentials: ConnectorCredential | None = None,
        *,
        limit: int = 100,
    ) -> list[NormalizedListing]:
        return []


CONNECTOR_REGISTRY: dict[str, BaseMarketplaceConnector] = {
    ConnectorType.COPART.value: CopartConnector(),
    ConnectorType.IAAI.value: IAAIConnector(),
    ConnectorType.AUTORIA.value: AutoRiaConnector(),
    ConnectorType.OLX_AUTO.value: OlxAutoConnector(),
    ConnectorType.MOBILE_DE.value: MobileDeConnector(),
    ConnectorType.LOCAL_DEALER.value: LocalDealerConnector(),
}


def get_connector(connector_type: str) -> BaseMarketplaceConnector:
    connector = CONNECTOR_REGISTRY.get(connector_type)
    if connector is None:
        raise ValueError(f"Unknown connector type: {connector_type}")
    return connector

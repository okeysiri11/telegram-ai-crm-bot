# Partner integrations bridge — thin facade over PartnerAPIService.

from __future__ import annotations

from applications.agro_marketplace.partner_api.service import PartnerAPIService, partner_api_service
from applications.agro_marketplace.portal.models import PartnerConnection, PartnerType


class PartnerIntegrationsBridge:
    def __init__(self, partners: PartnerAPIService | None = None) -> None:
        self._partners = partners or partner_api_service

    async def connect_bank(self, name: str, **config) -> PartnerConnection:
        return await self._partners.connect(
            PartnerConnection(partner_type=PartnerType.BANK, partner_name=name, config=dict(config))
        )

    async def connect_insurance(self, name: str, **config) -> PartnerConnection:
        return await self._partners.connect(
            PartnerConnection(partner_type=PartnerType.INSURANCE, partner_name=name, config=dict(config))
        )

    async def connect_logistics(self, name: str, **config) -> PartnerConnection:
        return await self._partners.connect(
            PartnerConnection(partner_type=PartnerType.LOGISTICS, partner_name=name, config=dict(config))
        )

    def call(self, partner_type: str, action: str = "default", **kwargs):
        return self._partners.invoke(partner_type, action, **kwargs)


partner_integrations = PartnerIntegrationsBridge()

# Order tracking helpers for marketplace trading orders.

from __future__ import annotations

from applications.agro_marketplace.marketplace.engine import MarketplaceEngine, marketplace_engine
from applications.agro_marketplace.marketplace.models import MarketplaceOrder


class MarketplaceOrderService:
    def __init__(self, marketplace: MarketplaceEngine | None = None) -> None:
        self._marketplace = marketplace or marketplace_engine

    def create(self, order: MarketplaceOrder) -> MarketplaceOrder:
        return self._marketplace.create_order(order)

    def list_orders(self) -> list[MarketplaceOrder]:
        return self._marketplace.list_orders()

    def get(self, order_id: str) -> MarketplaceOrder:
        return self._marketplace.get_order(order_id)

    async def confirm(self, order_id: str) -> MarketplaceOrder:
        return await self._marketplace.confirm_order(order_id)


marketplace_order_service = MarketplaceOrderService()

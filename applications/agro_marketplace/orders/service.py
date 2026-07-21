# OrderService — orders, offers, contracts.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.shared.events import ContractSignedEvent, OrderCreatedEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import (
    Contract,
    ContractStatus,
    Offer,
    Order,
    OrderStatus,
)
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class OrderService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_orders(self, *, status: OrderStatus | None = None) -> list[Order]:
        items = self._store.orders.list_all()
        if status:
            items = [o for o in items if o.status == status]
        return items

    def get_order(self, order_id: str) -> Order:
        order = self._store.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        return order

    async def create_order(self, order: Order) -> Order:
        if order.quantity <= 0:
            raise ValidationError("quantity must be positive")
        product = self._store.products.get(order.product_id)
        if product is None:
            raise NotFoundError("Product", order.product_id)
        if not order.farmer_id:
            order.farmer_id = product.farmer_id
        if not order.unit_price:
            order.unit_price = product.price
        order.status = OrderStatus.PLACED
        order.updated_at = time.time()
        saved = self._store.orders.save(order.order_id, order)
        await publish(
            OrderCreatedEvent(
                order_id=saved.order_id,
                buyer_id=saved.buyer_id,
                product_id=saved.product_id,
                quantity=saved.quantity,
            )
        )
        return saved

    def create_offer(self, offer: Offer) -> Offer:
        return self._store.offers.save(offer.offer_id, offer)

    def list_offers(self, *, product_id: str | None = None) -> list[Offer]:
        items = self._store.offers.list_all()
        if product_id:
            items = [o for o in items if o.product_id == product_id]
        return items

    def create_contract(self, contract: Contract) -> Contract:
        self.get_order(contract.order_id)
        return self._store.contracts.save(contract.contract_id, contract)

    async def sign_contract(self, contract_id: str) -> Contract:
        contract = self._store.contracts.get(contract_id)
        if contract is None:
            raise NotFoundError("Contract", contract_id)
        contract.status = ContractStatus.SIGNED
        contract.signed_at = time.time()
        saved = self._store.contracts.save(contract_id, contract)
        await publish(ContractSignedEvent(contract_id=saved.contract_id, order_id=saved.order_id))
        return saved


order_service = OrderService()

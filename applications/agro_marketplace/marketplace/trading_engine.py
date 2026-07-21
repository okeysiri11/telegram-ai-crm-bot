# TradingEngine — RFQ, sessions, contract lifecycle, trade history facade.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.marketplace.events import ContractPreparedEvent
from applications.agro_marketplace.marketplace.models import (
    ContractLifecycle,
    PriceRequest,
    TradeContract,
    TradingSession,
)
from applications.agro_marketplace.marketplace.workflow import TradingWorkflowBridge, trading_workflow
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class TradingEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: TradingAIIntegration | None = None,
        workflow: TradingWorkflowBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or trading_ai
        self._workflow = workflow or trading_workflow

    def create_rfq(self, rfq: PriceRequest) -> PriceRequest:
        if rfq.quantity <= 0:
            raise ValidationError("quantity must be positive")
        return self._store.price_requests.save(rfq.rfq_id, rfq)

    def list_rfqs(self, *, status: str | None = None) -> list[PriceRequest]:
        items = self._store.price_requests.list_all()
        if status:
            items = [r for r in items if r.status == status]
        return items

    def respond_to_rfq(self, rfq_id: str, offer_id: str) -> PriceRequest:
        rfq = self._store.price_requests.get(rfq_id)
        if rfq is None:
            raise NotFoundError("PriceRequest", rfq_id)
        if offer_id not in rfq.responses:
            rfq.responses.append(offer_id)
        return self._store.price_requests.save(rfq_id, rfq)

    def open_session(self, session: TradingSession) -> TradingSession:
        return self._store.trading_sessions.save(session.session_id, session)

    def list_sessions(self) -> list[TradingSession]:
        return self._store.trading_sessions.list_all()

    def close_session(self, session_id: str) -> TradingSession:
        session = self._store.trading_sessions.get(session_id)
        if session is None:
            raise NotFoundError("TradingSession", session_id)
        session.status = "closed"
        session.closed_at = time.time()
        return self._store.trading_sessions.save(session_id, session)

    async def prepare_contract(
        self,
        *,
        order_id: str,
        negotiation_id: str = "",
        parties: list[str] | None = None,
        terms: dict[str, Any] | None = None,
    ) -> TradeContract:
        order = self._store.marketplace_orders.get(order_id)
        if order is None:
            raise NotFoundError("MarketplaceOrder", order_id)
        contract = TradeContract(
            order_id=order_id,
            negotiation_id=negotiation_id,
            parties=parties or [order.buyer_id, order.seller_id],
            terms=terms
            or {
                "quantity": order.quantity,
                "unit_price": order.unit_price,
                "currency": order.currency,
                "total": order.total,
            },
            status=ContractLifecycle.PREPARED,
            prepared_at=time.time(),
        )
        saved = self._store.trade_contracts.save(contract.contract_id, contract)
        from applications.agro_marketplace.shared.models import Contract, ContractStatus

        self._store.contracts.save(
            saved.contract_id,
            Contract(
                contract_id=saved.contract_id,
                order_id=saved.order_id,
                parties=list(saved.parties),
                status=ContractStatus.PENDING_SIGNATURE,
                terms=dict(saved.terms),
            ),
        )
        await self._workflow.start_contract_workflow(saved.contract_id)
        await publish(
            ContractPreparedEvent(
                contract_id=saved.contract_id,
                order_id=saved.order_id,
                negotiation_id=saved.negotiation_id,
            )
        )
        return saved

    def get_contract(self, contract_id: str) -> TradeContract:
        contract = self._store.trade_contracts.get(contract_id)
        if contract is None:
            raise NotFoundError("TradeContract", contract_id)
        return contract

    def list_contracts(self) -> list[TradeContract]:
        return self._store.trade_contracts.list_all()

    async def sign_contract(self, contract_id: str) -> TradeContract:
        contract = self.get_contract(contract_id)
        contract.status = ContractLifecycle.SIGNED
        contract.signed_at = time.time()
        return self._store.trade_contracts.save(contract_id, contract)

    def activate_contract(self, contract_id: str) -> TradeContract:
        contract = self.get_contract(contract_id)
        contract.status = ContractLifecycle.ACTIVE
        return self._store.trade_contracts.save(contract_id, contract)

    def complete_contract(self, contract_id: str) -> TradeContract:
        contract = self.get_contract(contract_id)
        contract.status = ContractLifecycle.COMPLETED
        return self._store.trade_contracts.save(contract_id, contract)

    def trade_history(self) -> dict[str, Any]:
        return {
            "orders": [o.to_dict() for o in self._store.marketplace_orders.list_all()],
            "contracts": [c.to_dict() for c in self._store.trade_contracts.list_all()],
            "deals": [d.to_dict() for d in self._store.marketplace_deals.list_all()],
            "rfqs": [r.to_dict() for r in self._store.price_requests.list_all()],
            "sessions": [s.to_dict() for s in self._store.trading_sessions.list_all()],
        }

    async def price_recommendation(self, offer_id: str) -> dict[str, Any]:
        offer = self._store.sales_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("SalesOffer", offer_id)
        prices = [
            o.price for o in self._store.sales_offers.list_all() if o.crop_id == offer.crop_id and o.price > 0
        ]
        avg = sum(prices) / len(prices) if prices else 0.0
        return await self._ai.recommend_price(offer, market_avg=avg)


trading_engine = TradingEngine()

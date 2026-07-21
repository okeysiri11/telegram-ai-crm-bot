# ContractService — trade contract lifecycle.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.marketplace.models import TradeContract
from applications.agro_marketplace.marketplace.trading_engine import TradingEngine, trading_engine


class ContractService:
    def __init__(self, trading: TradingEngine | None = None) -> None:
        self._trading = trading or trading_engine

    async def prepare(
        self,
        *,
        order_id: str,
        negotiation_id: str = "",
        parties: list[str] | None = None,
        terms: dict[str, Any] | None = None,
    ) -> TradeContract:
        return await self._trading.prepare_contract(
            order_id=order_id,
            negotiation_id=negotiation_id,
            parties=parties,
            terms=terms,
        )

    async def sign(self, contract_id: str) -> TradeContract:
        return await self._trading.sign_contract(contract_id)

    def activate(self, contract_id: str) -> TradeContract:
        return self._trading.activate_contract(contract_id)

    def complete(self, contract_id: str) -> TradeContract:
        return self._trading.complete_contract(contract_id)

    def list_contracts(self) -> list[TradeContract]:
        return self._trading.list_contracts()


contract_service = ContractService()

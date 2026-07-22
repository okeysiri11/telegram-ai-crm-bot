# Import / Export Engine — duties, taxes, permissions, certificates.

from __future__ import annotations

from applications.auto_marketplace.international.engine import InternationalEngine, international_engine
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import TradeShipment


DUTY_RATES = {
    "US": 0.025,
    "EU": 0.10,
    "TR": 0.15,
    "AE": 0.05,
    "GB": 0.08,
}


class ImportExportEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        international: InternationalEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._international = international or international_engine

    def calculate_duties(self, *, vehicle_value: float, destination_country: str) -> dict:
        if vehicle_value <= 0:
            raise ValidationError("vehicle_value must be positive")
        rate = DUTY_RATES.get(destination_country.upper(), 0.12)
        duties = round(vehicle_value * rate, 2)
        taxes = round(vehicle_value * 0.08, 2)
        return {
            "vehicle_value": vehicle_value,
            "destination_country": destination_country.upper(),
            "duty_rate": rate,
            "duties": duties,
            "taxes": taxes,
            "total": round(duties + taxes, 2),
        }

    def create_trade(self, trade: TradeShipment, *, vehicle_value: float = 0.0) -> TradeShipment:
        if trade.direction not in {"import", "export"}:
            raise ValidationError("direction must be import or export")
        if not trade.origin_country or not trade.destination_country:
            raise ValidationError("origin_country and destination_country are required")
        trade.regulations = self._international.regulations(trade.origin_country, trade.destination_country)
        if vehicle_value > 0:
            calc = self.calculate_duties(vehicle_value=vehicle_value, destination_country=trade.destination_country)
            trade.duties = calc["duties"]
            trade.taxes = calc["taxes"]
        if trade.direction == "import":
            trade.permissions = ["import_license"]
            trade.certificates = ["certificate_of_conformity"]
        else:
            trade.permissions = ["export_permit"]
            trade.certificates = ["export_certificate"]
        trade.status = "quoted"
        return self._store.trade_shipments.save(trade.trade_id, trade)

    def get(self, trade_id: str) -> TradeShipment:
        item = self._store.trade_shipments.get(trade_id)
        if item is None:
            raise NotFoundError("TradeShipment", trade_id)
        return item

    def approve(self, trade_id: str) -> TradeShipment:
        trade = self.get(trade_id)
        trade.status = "approved"
        return self._store.trade_shipments.save(trade_id, trade)

    def list_trades(self, *, direction: str = "") -> list[TradeShipment]:
        items = self._store.trade_shipments.list_all()
        if direction:
            items = [t for t in items if t.direction == direction]
        return items

    def metrics(self) -> dict:
        items = self._store.trade_shipments.list_all()
        return {
            "trades": len(items),
            "imports": len([t for t in items if t.direction == "import"]),
            "exports": len([t for t in items if t.direction == "export"]),
        }


import_export_engine = ImportExportEngine()

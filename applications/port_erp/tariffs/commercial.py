# Commercial Tariff Engine — port/terminal fees (distinct from customs HS tariffs).

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.finance.events import TariffUpdatedEvent
from applications.port_erp.finance.models import CommercialTariff, FeeType, PricingMode
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class CommercialTariffEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def fee_types(self) -> list[str]:
        return [f.value for f in FeeType]

    def pricing_modes(self) -> list[str]:
        return [p.value for p in PricingMode]

    def register(self, tariff: CommercialTariff) -> CommercialTariff:
        if not tariff.name:
            raise ValidationError("name is required")
        if tariff.rate < 0:
            raise ValidationError("rate must be non-negative")
        return self._store.commercial_tariffs.save(tariff.tariff_id, tariff)

    def get(self, tariff_id: str) -> CommercialTariff:
        item = self._store.commercial_tariffs.get(tariff_id)
        if item is None:
            raise NotFoundError("CommercialTariff", tariff_id)
        return item

    def list_tariffs(
        self,
        *,
        fee_type: FeeType | None = None,
        terminal_id: str | None = None,
    ) -> list[CommercialTariff]:
        items = [t for t in self._store.commercial_tariffs.list_all() if t.is_active]
        if fee_type:
            items = [t for t in items if t.fee_type == fee_type]
        if terminal_id:
            items = [t for t in items if t.terminal_id == terminal_id]
        return items

    async def update_rate(self, tariff_id: str, *, rate: float) -> CommercialTariff:
        tariff = self.get(tariff_id)
        if rate < 0:
            raise ValidationError("rate must be non-negative")
        tariff.rate = rate
        saved = self._store.commercial_tariffs.save(tariff_id, tariff)
        await publish(
            TariffUpdatedEvent(
                tariff_id=tariff_id, fee_type=saved.fee_type.value, rate=saved.rate
            )
        )
        return saved

    def quote(
        self,
        *,
        fee_type: FeeType | str,
        quantity: float = 1.0,
        terminal_id: str = "",
        volume: float = 0.0,
        priority: bool = False,
        emergency: bool = False,
    ) -> dict:
        ftype = FeeType(fee_type) if isinstance(fee_type, str) else fee_type
        candidates = self.list_tariffs(fee_type=ftype, terminal_id=terminal_id or None)
        if not candidates:
            candidates = self.list_tariffs(fee_type=ftype)
        if not candidates:
            raise ValidationError(f"no tariff for {ftype.value}")
        tariff = candidates[0]
        if emergency:
            emergency_tariffs = [t for t in candidates if t.pricing_mode == PricingMode.EMERGENCY]
            tariff = emergency_tariffs[0] if emergency_tariffs else tariff
        elif priority:
            priority_tariffs = [t for t in candidates if t.pricing_mode == PricingMode.PRIORITY]
            tariff = priority_tariffs[0] if priority_tariffs else tariff
        rate = tariff.rate
        if tariff.pricing_mode == PricingMode.SEASONAL:
            rate *= 1.15
        if tariff.pricing_mode == PricingMode.DYNAMIC:
            rate *= 1.0 + min(0.5, quantity * 0.02)
        if tariff.pricing_mode == PricingMode.VOLUME_DISCOUNT or (
            volume and volume >= tariff.min_qty > 0
        ):
            rate *= max(0.0, 1.0 - tariff.discount_pct / 100.0)
        amount = round(rate * quantity, 2)
        return {
            "tariff_id": tariff.tariff_id,
            "fee_type": ftype.value,
            "quantity": quantity,
            "unit_rate": round(rate, 4),
            "amount": amount,
            "currency": tariff.currency,
            "pricing_mode": tariff.pricing_mode.value,
        }


commercial_tariff_engine = CommercialTariffEngine()

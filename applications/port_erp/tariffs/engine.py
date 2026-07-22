# Tariff Engine — HS code duty / VAT rates and duty calculation.

from __future__ import annotations

from applications.port_erp.customs.models import TariffRate
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class TariffEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, tariff: TariffRate) -> TariffRate:
        if not tariff.hs_code:
            raise ValidationError("hs_code is required")
        return self._store.tariff_rates.save(tariff.tariff_id, tariff)

    def get(self, tariff_id: str) -> TariffRate:
        item = self._store.tariff_rates.get(tariff_id)
        if item is None:
            raise NotFoundError("TariffRate", tariff_id)
        return item

    def find_by_hs(self, hs_code: str, *, country: str = "") -> TariffRate | None:
        items = [t for t in self._store.tariff_rates.list_all() if t.hs_code == hs_code]
        if country:
            matched = [t for t in items if t.country == country]
            if matched:
                return matched[0]
        return items[0] if items else None

    def list_tariffs(self, *, country: str | None = None) -> list[TariffRate]:
        items = self._store.tariff_rates.list_all()
        if country:
            items = [t for t in items if t.country == country]
        return items

    def calculate_duties(self, *, hs_code: str, value: float, country: str = "") -> dict:
        if value < 0:
            raise ValidationError("value must be non-negative")
        tariff = self.find_by_hs(hs_code, country=country)
        if tariff is None:
            return {
                "hs_code": hs_code,
                "value": value,
                "duty": 0.0,
                "vat": 0.0,
                "total": value,
                "tariff_found": False,
            }
        duty = round(value * tariff.duty_rate_pct / 100.0, 2)
        vat = round((value + duty) * tariff.vat_rate_pct / 100.0, 2)
        return {
            "hs_code": hs_code,
            "value": value,
            "duty_rate_pct": tariff.duty_rate_pct,
            "vat_rate_pct": tariff.vat_rate_pct,
            "duty": duty,
            "vat": vat,
            "total": round(value + duty + vat, 2),
            "tariff_found": True,
            "tariff_id": tariff.tariff_id,
        }


tariff_engine = TariffEngine()

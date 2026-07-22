# Currencies + Taxes helpers.

from __future__ import annotations

from applications.port_erp.finance.models import ExchangeRate, TaxRate
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class CurrencyEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def set_rate(self, rate: ExchangeRate) -> ExchangeRate:
        if rate.rate <= 0:
            raise ValidationError("rate must be positive")
        return self._store.exchange_rates.save(rate.rate_id, rate)

    def list_rates(self) -> list[ExchangeRate]:
        return self._store.exchange_rates.list_all()

    def convert(self, amount: float, *, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return round(amount, 2)
        rates = self._store.exchange_rates.list_all()
        direct = next(
            (
                r
                for r in rates
                if r.base_currency == from_currency and r.quote_currency == to_currency
            ),
            None,
        )
        if direct:
            return round(amount * direct.rate, 2)
        inverse = next(
            (
                r
                for r in rates
                if r.base_currency == to_currency and r.quote_currency == from_currency
            ),
            None,
        )
        if inverse:
            return round(amount / inverse.rate, 2)
        raise ValidationError(f"no exchange rate for {from_currency}->{to_currency}")


class TaxEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, tax: TaxRate) -> TaxRate:
        if tax.rate_pct < 0:
            raise ValidationError("rate_pct must be non-negative")
        return self._store.tax_rates.save(tax.tax_id, tax)

    def list_taxes(self, *, country: str | None = None) -> list[TaxRate]:
        items = self._store.tax_rates.list_all()
        if country:
            items = [t for t in items if t.country == country]
        return items

    def calculate(self, amount: float, *, country: str = "", tax_name: str = "VAT") -> dict:
        taxes = self.list_taxes(country=country or None)
        tax = next((t for t in taxes if t.name == tax_name), taxes[0] if taxes else None)
        rate = tax.rate_pct if tax else 0.0
        tax_amount = round(amount * rate / 100.0, 2)
        return {
            "base": amount,
            "tax_name": tax.name if tax else tax_name,
            "rate_pct": rate,
            "tax_amount": tax_amount,
            "total": round(amount + tax_amount, 2),
        }


currency_engine = CurrencyEngine()
tax_engine = TaxEngine()

"""Multi-currency — rates, conversion, historical FX, base currency."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MultiCurrency:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.base_currency = DEFAULT_CONFIG.base_currency

    def set_base_currency(self, *, code: str) -> dict[str, Any]:
        if not code:
            raise ValidationError("currency code required")
        self.base_currency = code.upper().strip()
        cid = _id("fe_base")
        return self.store.financial_config.save(
            "base_currency",
            {
                "config_id": cid,
                "key": "base_currency",
                "value": self.base_currency,
                "updated_at": _now(),
            },
        )

    def register_rate(
        self,
        *,
        from_currency: str,
        to_currency: str,
        rate: float,
        as_of: str = "",
    ) -> dict[str, Any]:
        if not from_currency or not to_currency:
            raise ValidationError("from_currency and to_currency required")
        if float(rate) <= 0:
            raise ValidationError("rate must be positive")
        rid = _id("fe_fx")
        from_c = from_currency.upper().strip()
        to_c = to_currency.upper().strip()
        as_of_v = as_of or _now()[:10]
        row = self.store.exchange_rates.save(
            rid,
            {
                "rate_id": rid,
                "from_currency": from_c,
                "to_currency": to_c,
                "rate": float(rate),
                "as_of": as_of_v,
                "created_at": _now(),
            },
        )
        hid = _id("fe_hfx")
        self.store.historical_rates.save(
            hid,
            {
                "historical_id": hid,
                "from_currency": from_c,
                "to_currency": to_c,
                "rate": float(rate),
                "as_of": as_of_v,
                "created_at": _now(),
            },
        )
        return row

    def convert(
        self,
        *,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate: float | None = None,
    ) -> dict[str, Any]:
        from_c = from_currency.upper().strip()
        to_c = to_currency.upper().strip()
        if not from_c or not to_c:
            raise ValidationError("from_currency and to_currency required")
        amt = float(amount)
        if from_c == to_c:
            fx_rate = 1.0
        elif rate is not None:
            fx_rate = float(rate)
            if fx_rate <= 0:
                raise ValidationError("rate must be positive")
        else:
            match = None
            for row in self.store.exchange_rates.list_all():
                if row["from_currency"] == from_c and row["to_currency"] == to_c:
                    match = row
            if match is None:
                raise ValidationError(f"no exchange rate for {from_c}/{to_c}")
            fx_rate = float(match["rate"])
        converted = round(amt * fx_rate, 6)
        cid = _id("fe_conv")
        return self.store.fx_conversions.save(
            cid,
            {
                "conversion_id": cid,
                "amount": amt,
                "from_currency": from_c,
                "to_currency": to_c,
                "rate": fx_rate,
                "converted_amount": converted,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "base_currency": self.base_currency,
            "exchange_rates": self.store.exchange_rates.count(),
            "conversions": self.store.fx_conversions.count(),
            "historical_rates": self.store.historical_rates.count(),
        }

"""Payment Gateway — Sprint 22.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_commerce.models import PAYMENT_PROVIDERS


class PaymentGateway:
    def charge(
        self,
        *,
        provider: str,
        amount: float,
        currency: str = "USD",
        reference: str = "",
    ) -> dict[str, Any]:
        if provider not in PAYMENT_PROVIDERS:
            raise ValueError(f"unsupported payment provider: {provider}")
        if amount <= 0:
            raise ValueError("charge amount must be positive")
        return {
            "provider": provider,
            "amount": float(amount),
            "currency": currency,
            "reference": reference or None,
            "status": "authorized",
            "pluggable": True,
            "business_logic_coupled": False,
        }

    def providers(self) -> list[str]:
        return list(PAYMENT_PROVIDERS)
